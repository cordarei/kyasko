#lang racket

(define test-string "This is a test, input U.S.A. It consists of two sentences.")


(define (token-word s k)
  (match (regexp-match #px"^(\\w+)(.*)$" s)
    [(list _ word rest)
     (list (cons word (k rest)))]
    [#f
     '()]))

(define (token-abbrev s k)
  (match (regexp-match #px"^(([A-Za-z]\\.)+)(.*)$" s)
    [(list _ word _ rest)
     (list (cons word (k rest))
           (cons word (cons "." (k rest))))]
    [#f
     '()]))

(define (tokenize s)
  (define (skip-ws s) (tokenize (string-trim s #:right? #f)))
  (append (token-word s skip-ws) (token-abbrev s skip-ws)))