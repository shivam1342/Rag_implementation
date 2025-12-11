from rag_core import rag_answer

query = input("Enter your question: ")
answer = rag_answer(query)

print("\n--- ANSWER ---\n")
print(answer)
