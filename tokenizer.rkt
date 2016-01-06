#lang racket


(require racket/control)

(define (run thunk return . arguments)
  (reset (return (apply thunk arguments))))

(struct Maybe () #:transparent)
(struct Nothing Maybe () #:transparent)
(struct Some Maybe (value) #:transparent)

(define (nothing) (shift k (Nothing)))

#;(define (inject-values . values)
  (shift k (append-map k values)))

(define (make-operator bind operator)
  (λ arguments
    (shift k (bind (apply operator arguments) k))))

(define (list-bind x k) (append-map k x))
(define inject-values (make-operator list-bind list))


(define-syntax (run-list stx)
  (syntax-case stx ()
    [(_ body ...)
     #'(run (λ () body ...) list)]))


(define test-string "This is a test, input U.S.A. It consists of two sentences.")

(define (string-empty? s) (= 0 (string-length s)))

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


(define-syntax (match-token stx)
  (syntax-case stx ()
    [(_ obj cases ...)
     #'(append
        (match obj cases [_ '()]) ...
        )]))

(define (tokenize2 s)
  (let rec ([input s]
            [tokens '()])
    (match input
      ["" (list (reverse tokens))]
      [(pregexp #px"^(\\w+)(.*)$" (list _ word rest))
       (rec (string-trim rest #:right? #f) (cons word tokens))]
      [_ '()])))

(define (tokenize3 s)
  (let rec ([input s]
            [tokens '()])
    (set! input (string-trim input #:right? #f))
    (if (string-empty? input)
        (list (reverse tokens))
        (match-token input
                     ;; simple word token (no punct)
                     [(pregexp #px"^(\\w+)(.*)$" (list _ word rest))
                      (rec rest (cons word tokens))]
                     ;; single punctuation character, comma etc
                     [(pregexp #px"^([^\\w\\s])(.*)$" (list _ char rest))
                      #:when (not (regexp-match #px"^\\w" rest))
                      (rec rest (cons char tokens))]
                     ;; abbreviation (no sentence boundary)
                     [(pregexp #px"^(([A-Za-z]\\.)+)(.*)$" (list _ word _ rest))
                      (rec rest (cons word tokens))]
                     ;; abbreviation + sentence boundary
                     [(pregexp #px"^(([A-Za-z]\\.)+)(.*)$" (list _ word _ rest))
                      (rec rest (cons "." (cons word tokens)))]
                     ))))




(define test-sherlock
  "Mr. Sherlock Holmes, who was usually very late in the mornings,\nsave upon those not infrequent occasions when he was up all night, was seated at the breakfast table.\nI stood upon the hearth-rug and picked up the stick which our visitor had left behind him the night before. It was a fine, thick piece of wood, bulbous-headed,\nof the sort which is known as a “Penang lawyer.” Just under the head was a broad silver band nearly an inch across. “To James Mortimer, M.R.C.S., from his friends of the C.C.H.,” was engraved upon it, with the date “1884.” It was just such a stick as the old-fashioned family practitioner used to carry—dignified, solid, and reassuring.")