# Retrieval Evaluation

- 질문 수 : 30 (기술별 15)
- 최고 Dense 임베딩 : snowflake/snowflake-arctic-embed-s

| Retriever | Hit@1 | Hit@3 | Hit@5 | MRR@5 |
|---|---|---|---|---|
| Dense · BAAI/bge-small-en-v1.5 | 0.6 | 0.733 | 0.8 | 0.678 |
| Dense · sentence-transformers/all-MiniLM-L6-v2 | 0.6 | 0.733 | 0.767 | 0.669 |
| Dense · snowflake/snowflake-arctic-embed-s | 0.733 | 0.933 | 1.0 | 0.844 |
| Sparse · BM25 | 0.867 | 0.933 | 0.967 | 0.901 |
| Hybrid · BM25 + snowflake/snowflake-arctic-embed-s | 0.867 | 0.967 | 0.967 | 0.917 |
