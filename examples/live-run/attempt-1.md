## Start here

Imagine an open-book exam in college. Instead of answering only from memory, you open your notebook, find the right page, and write the answer. RAG works like this open-book test for computers. It helps computer programs answer your questions by reading helpful notes first.

## What it is

AI means artificial intelligence, which is software that does human tasks like reading or writing text [S1]. A language model is a type of AI software trained to write sentences [S1].

RAG stands for Retrieval-Augmented Generation [S1]. 
- **Retrieval** means finding useful information.
- **Augmented** means helped by extra information.
- **Generation** means writing out an answer.

So, RAG is a method where an AI writer is helped by looking up facts before it speaks [S1, S2].

## Why it matters

A regular language model answers only from what the model learned in past training [S2]. It might guess when it does not know something fresh or specific. Looking up notes at answer time helps the system use new or special facts without changing what the model learned during its past training [S1, S2]. This improves factual quality and cuts down made-up facts [S1, S2].

## How it works

The full process takes three simple steps:
1. **You ask a question:** You type what you need to know.
2. **The system finds notes:** The computer searches stored documents, web pages, or local files for matching pieces [S1]. An internet search is not always required [S1].
3. **The system writes the answer:** The computer gives your question along with those found notes to the language model [S1]. The model uses those notes to write out a clear reply [S1, S2].

## A worked example

Let us look at a fictional college example.

Suppose you ask: "What is the last date to submit the physics assignment?"

Without notes, the AI might guess: "It is probably Friday." That guess could be wrong.

Now, here is a fictional college notice: *"Fictional Notice: Physics Assignment 2 must be submitted to Room 104 by 14th August at 4 PM."*

The RAG system finds this exact notice. It sends your question and this notice together to the language model. The model reads the notice and replies correctly: "The last date to submit the physics assignment is 14th August by 4 PM."

## What can go wrong

RAG does not guarantee correct answers every time [S1, S2]. Mistakes can happen if the notes are wrong, old, or missing [S1]. If the notice has the wrong date, the answer can also be wrong [S1]. 

Also, if you ask: "What is the chemistry homework?", the physics notice does not help. In that case, a good RAG system should simply say: "The provided notes do not contain this answer," instead of guessing [S1].

## Check yourself

Try these three questions:

1. What does the word "augmented" mean in RAG?
2. Fictional library notice: *"The library closes at 6 PM on Saturdays."* A student asks: "When does the library close on Saturday?" What will a RAG system do to answer?
3. Fictional bus notice: *"Bus 12 runs between the railway station and the market."* A passenger asks: "What is the ticket price for Bus 12?" What should a good RAG system reply?

---

**Answers:**
1. "Augmented" means helped by extra information.
2. The system retrieves the library notice, attaches it to the student's question, and uses it to answer: "The library closes at 6 PM on Saturdays."
3. It should state that the provided notes do not contain the answer, because ticket prices are not mentioned.

## Recap

RAG combines finding saved notes with text generation [S1, S2]. It helps an AI answer using real documents rather than guessing [S1]. Always remember: if source notes are missing or incorrect, errors can still happen [S1].

RAG always gives correct answers, even when its source notes are wrong.
