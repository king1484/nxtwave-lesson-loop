# Introduction to RAG

## Start here

Imagine you want to know when your college library opens. You ask a friend. Your friend guesses, “Maybe 9 am.” You check the college notice. It says 10 am.

Which answer would you trust more? Reading the right note helps. An AI tool can use a similar idea. AI means artificial intelligence: software that can do tasks such as writing text.

By the end, you will know what RAG means. You will also explain its steps and know when it should avoid guessing. You do not need to know coding.

## What it is

A query uses the model's learned parameters to return a response.

RAG stands for Retrieval-Augmented Generation. The name sounds difficult. The idea is easier:

- **Retrieval** means finding useful information.
- **Augmented** means helped by something extra.
- **Generation** means creating an answer.

RAG finds useful information, gives it to a language model, and asks the model to write an answer. A language model is AI software trained to produce language. [S1]

Think of answering a question with your notes open. This is an analogy, or comparison. The computer searches and writes text; it does not think exactly like your friend.

## Why it matters

A language model may not know your college's latest notice. It may give an answer that sounds right but is wrong.

RAG lets an application provide relevant information from sources such as documents or a database. A database is an organised store of information. This can help answer questions about information the model does not already have. [S1]

The source must actually contain the needed information. RAG cannot make a missing notice appear.

## How it works

There are three basic steps:

1. **Find.** Use the question to search the available notes. Select the useful parts.
2. **Add.** Send those parts together with the question to the language model.
3. **Answer.** Ask the model to write an answer using those parts. [S1]

The notes given with a question are called its **context**. Here, context means information provided to help answer that question.

The search can use your own saved documents. It does not have to search the internet. Looking up a note does not itself retrain the model. Retraining means changing what a model has learned through more training. [S2]

## A worked example

This college and its notice are fictional. They are made up for learning.

**Available note:** “The college library opens at 10 am on Monday. Students must carry their ID card.”

**Your question:** “When does the library open on Monday?”

Without that note, the model might guess “9 am.” That guess has no support here.

With RAG, the application finds this useful part: “The college library opens at 10 am on Monday.”

It sends that text and your question to the model. The model can then answer: “The library opens at 10 am on Monday, according to the notice.”

Notice that the answer follows the note. It does not invent a time.

## What can go wrong

Now ask: “Does the library open on Sunday?” The note says nothing about Sunday.

A suitable answer is: “I do not know from this notice. Please check the Sunday timings.” The application should ask for this behaviour instead of encouraging a guess.

RAG can still make mistakes. It may find the wrong note. A note may be old or incorrect. The model may also use the information badly. Important answers still need checking. [S1]

## Check yourself

Try these before reading the answers.

1. What does the retrieval step do?
2. A fictional fee notice says, “Pay the exam fee by Friday.” You ask, “What is the deadline?” Describe the three steps.
3. That fee notice says nothing about the amount. Should the model invent an amount?

**Answer key**

1. It finds information useful for the question.
2. Find the fee notice. Add its Friday deadline to the question. Write an answer saying the deadline is Friday.
3. No. It should say the amount is not given and suggest checking the full notice.

## Recap

RAG helps a language model answer using information found in sources. Remember: **find, add, answer**.

Good notes can help. Missing or wrong notes can cause problems. An honest “I do not know” is better than an unsupported guess.
