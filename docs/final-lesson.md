## Start here

Imagine an open-book exam in college. Instead of answering only from memory, you open your notebook, find the right page, and write your answer. RAG works like this open-book test for computers. It helps computer software answer your questions by reading helpful notes first.

## What it is

AI means artificial intelligence, which is software that does tasks like reading or writing text [S1]. A language model is a type of AI software trained to produce written language [S1].

RAG stands for Retrieval-Augmented Generation [S1].
- **Retrieval** means finding useful information.
- **Augmented** means helped by extra information.
- **Generation** means writing out an answer.

RAG combines finding relevant information in external sources with a language model that writes a response [S1, S2].

## Why it matters

A regular language model answers using only what the model learned in past training [S2]. It might guess when it does not know fresh or specialized details. Looking up notes at answer time provides new information without changing what the model learned in its training [S1, S2]. Supplying reference information at answer time and training a model are different operations [S2]. This process can improve factual quality and reduce made-up answers [S1, S2].

## How it works

The full process takes three clear steps:
1. **A question is asked:** You ask a question about a topic.
2. **The system finds notes:** The computer searches stored documents, web pages, or local files for matching pieces [S1]. An internet search is not always required [S1].
3. **The system writes the answer:** The computer provides the found notes alongside your question to the language model [S1]. The model uses those notes to generate a response [S1, S2].

## A worked example

Let us look at a fictional college situation.

Suppose you ask: "What is the last date to submit the physics assignment?"

Without any notes, the language model might guess blindly: "It is probably this Friday." That guess could be completely wrong.

Now consider this fictional notice: *"Fictional Notice: Physics Assignment 2 must be submitted to Room 104 by 14th August at 4 PM."*

The RAG system finds this exact notice piece. It sends your question together with this notice to the language model. The model reads the text and writes a supported reply: "The last date to submit the physics assignment is 14th August by 4 PM."

## What can go wrong

RAG does not guarantee correct answers [S1, S2]. Mistakes can still happen if the source notes are wrong, outdated, or missing [S1]. If the notice has an incorrect date, the model's answer can also be wrong [S1]. Therefore, notes should be checked rather than blindly trusted [S1].

Furthermore, if you ask: "What is the chemistry homework?", the physics notice has no helpful details. In that situation, a good RAG system should simply say: "The provided notes do not contain this answer," instead of guessing [S1].

## Check yourself

Try these three questions:

1. What does the word "augmented" mean in RAG?
2. Fictional library notice: *"The college library closes at 6 PM on Saturdays."* A student asks: "When does the library close on Saturday?" What will a RAG system do to answer?
3. Fictional bus notice: *"Bus 12 runs between the railway station and the market."* A passenger asks: "What is the ticket price for Bus 12?" What should a good RAG system reply?

---

**Answers:**
1. "Augmented" means helped by extra information.
2. The system finds the relevant library notice, gives that notice together with the question to the language model, and generates the answer: "The college library closes at 6 PM on Saturdays."
3. It should reply that the provided notes do not contain the answer, because ticket prices are not mentioned in the notice.

## Recap

RAG combines looking up saved notes with text generation [S1, S2]. It helps an AI answer using reference documents rather than guessing [S1]. Looking up notes does not change what the model learned in training [S2]. Remember that mistakes can still happen if notes are missing or incorrect [S1].

## Sources

- [S1] [Google Cloud: What is Retrieval-Augmented Generation?](https://cloud.google.com/use-cases/retrieval-augmented-generation)
- [S2] [Lewis et al.: Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks](https://arxiv.org/abs/2005.11401)
