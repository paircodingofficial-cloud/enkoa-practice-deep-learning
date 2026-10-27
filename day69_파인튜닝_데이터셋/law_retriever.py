"""새 질문에 답할 조문을 찾는 검색기 파일입니다(교안 01, 과제 01, 부록이 함께 씁니다).

하이브리드 검색 단원과 리랭킹·컨텍스트 압축 단원에서 배운 LangChain 방식을 그대로 씁니다.
- 키워드 검색: BM25Retriever, 한국어는 kiwi_tokenize(명사, 외국어, 숫자)로 나눕니다
- 의미 검색: OpenAI 임베딩(text-embedding-3-large, 768차원)을 넣은 Chroma 메모리 컬렉션
- 하이브리드: EnsembleRetriever가 두 검색의 순위를 RRF로 합칩니다(가중치 0.5씩, c=60)
- 재정렬: Cross-Encoder 리랭커(Qwen/Qwen3-Reranker-0.6B)가 후보를 질문과 함께 다시 점수 매겨 상위 top_n개만 남깁니다
  (build_retriever(..., use_rerank=False)로 끄면 재정렬 없이 하이브리드 검색의 후보를 그대로 돌려줍니다)

이 파일을 import 하기 전에 .env의 OPENAI_API_KEY를 읽어 두어야 합니다(임베딩 모델을 만들 때 키를 읽습니다).
"""
import torch
from kiwipiepy import Kiwi
from langchain_chroma import Chroma
from langchain_classic.retrievers import ContextualCompressionRetriever, EnsembleRetriever
from langchain_classic.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

# 키워드 검색과 의미 검색이 각각 찾을 후보 수(합치면 최대 2배)와, 재정렬 뒤 남길 조문 수의 기본값
CANDIDATE_K = 10
TOP_N = 5

# 문서와 질문을 같은 모델과 차원으로 임베딩합니다(리랭킹·컨텍스트 압축 단원과 같은 설정)
# check_embedding_ctx_length=False: 자동 길이 검사와 분할을 끄고 문단을 그대로 보냅니다
embedding_model = OpenAIEmbeddings(model="text-embedding-3-large", dimensions=768, check_embedding_ctx_length=False)

# 리랭커를 실행할 장치: NVIDIA GPU(cuda)가 있으면 cuda, 맥 GPU(mps)가 있으면 mps, 둘 다 없으면 CPU
# 리랭커는 질문마다 후보 조문을 하나씩 점수 매기므로 CPU에서는 질문 수백 개에 한 시간 가까이 걸립니다
if torch.cuda.is_available():
    DEVICE = "cuda"
elif torch.backends.mps.is_available():
    DEVICE = "mps"
else:
    DEVICE = "cpu"


def load_cross_encoder():
    """후보를 다시 점수 매기는 Cross-Encoder(Qwen3-Reranker-0.6B)를 불러와 돌려줍니다."""
    print("리랭커를 실행할 장치:", DEVICE)

    # 1) 장치와 최대 토큰 길이(max_length): 모델이 받을 수 있는 최대 길이(모델 카드의 문맥 길이 32K)까지 질문과 조문 한 쌍을 자르지 않고 읽습니다
    reranker_kwargs = {"device": DEVICE, "max_length": 32768}

    # 2) NVIDIA GPU에서는 16비트(float16)로 불러와 메모리와 시간을 줄입니다. 맥(mps)과 CPU는 기본 32비트 그대로 둡니다
    if DEVICE == "cuda":
        reranker_kwargs["model_kwargs"] = {"torch_dtype": torch.float16}

    # 3) 첫 실행에 모델 파일(약 1.2GB)을 내려받습니다. 재정렬을 끄면(use_rerank=False) 이 함수를 부르지 않습니다
    return HuggingFaceCrossEncoder(model_name="Qwen/Qwen3-Reranker-0.6B", model_kwargs=reranker_kwargs)


# 형태소 분석기는 한 번 준비해 문서와 질문에 같은 방식으로 씁니다
kiwi = Kiwi()


def kiwi_tokenize(text):
    """명사, 외국어, 숫자를 소문자 토큰 리스트로 돌려줍니다."""
    # N 계열은 명사, SL은 외국어, SN은 숫자입니다. 조사와 어미는 뺍니다
    words = []
    for token in kiwi.tokenize(text):
        if token.tag.startswith("N") or token.tag in {"SL", "SN"}:
            words.append(token.form.lower())
    return words


def make_documents(articles):
    """조문 딕셔너리 리스트를 doc_id, source가 메타데이터에 있는 Document 리스트로 바꿉니다."""
    documents = []
    for article in articles:
        # id는 Chroma 저장소가, metadata의 doc_id는 두 검색 결과를 합칠 때 같은 조문을 알아보는 데 씁니다
        document = Document(
            id=article["doc_id"],
            page_content=article["text"],
            metadata={"doc_id": article["doc_id"], "source": article["source"]},
        )
        documents.append(document)
    return documents


def build_hybrid(documents, collection_name, candidate_k):
    """BM25 키워드 검색과 Chroma 의미 검색을 RRF로 합친 하이브리드 검색기를 돌려줍니다."""
    # 1) 키워드 검색: 질문과 같은 낱말(조문 용어, 숫자)이 많은 문단을 찾습니다
    bm25 = BM25Retriever.from_documents(documents, preprocess_func=kiwi_tokenize, k=candidate_k)

    # 2) 의미 검색: 같은 이름의 메모리 컬렉션을 비우고 문단을 임베딩해 넣습니다(부를 때마다 다시 임베딩)
    vector_store = Chroma(collection_name=collection_name, embedding_function=embedding_model)
    vector_store.reset_collection()
    doc_ids = [document.metadata["doc_id"] for document in documents]
    vector_store.add_documents(documents, ids=doc_ids)
    dense = vector_store.as_retriever(search_kwargs={"k": candidate_k})

    # 3) 두 검색의 순위를 RRF로 합칩니다. weights의 순서는 retrievers의 순서와 같습니다
    return EnsembleRetriever(retrievers=[bm25, dense], weights=[0.5, 0.5], c=60, id_key="doc_id")


def build_retriever(articles, collection_name, candidate_k=CANDIDATE_K, top_n=TOP_N, use_rerank=True):
    """조문 리스트로 하이브리드 검색기를 만들고, use_rerank=True면 재정렬해 상위 top_n개만 돌려주는 검색기를 만듭니다."""
    # 1) 조문을 Document로 바꿉니다
    documents = make_documents(articles)

    # 2) 키워드 검색과 의미 검색이 각각 candidate_k개씩 찾은 후보를 합치는 하이브리드 검색기
    hybrid = build_hybrid(documents, collection_name, candidate_k)

    # 3) 재정렬을 끄면 하이브리드 검색의 후보(RRF 순서, 최대 candidate_k x 2개)를 그대로 돌려줍니다
    if not use_rerank:
        return hybrid

    # 4) 합친 후보를 Cross-Encoder로 다시 점수 매겨 상위 top_n개만 남기는 리랭커
    reranker = CrossEncoderReranker(model=load_cross_encoder(), top_n=top_n)

    # 5) 검색과 재정렬을 한 번에 하는 검색기. invoke(질문)는 관련 있는 순서의 Document 리스트를 돌려줍니다
    return ContextualCompressionRetriever(base_retriever=hybrid, base_compressor=reranker)
