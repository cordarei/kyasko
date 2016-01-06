#lang racket

;; https://github.com/epsil/gll/blob/master/README.md


(struct success (val rest) #:transparent)
(struct failure (rest) #:transparent)

(define (succeed val)
  (lambda (str)
    (success val str)))

(define (string match)
  (lambda (str)
    (let* ([len (min (string-length str) (string-length match))]
           [head (substring str 0 len)]
           [tail (substring str len)])
      (if (equal? match head)
          (success head tail)
          (failure str)))))

(define (alt a b)
  (lambda (str)
    (let ([result (a str)])
      (match result
        [(success val rest) result]
        [failure (b str)]))))

#;(define (seq a b)
  (lambda (str)
    (match (a str)
       [(success val1 rest1)
        (match (b rest1)
          [(success val2 rest2)
           (success (list val1 val2) rest2)]
          [failure failure])]
       [failure failure])))

(define (bind p fn)
  (lambda (str)
    (match (p str)
      [(success val rest)
       ((fn val) rest)]
      [failure failure])))

(define (seq a b)
  (bind a (lambda (x)
            (bind b (lambda (y)
                      (succeed (list x y)))))))


(define article
  (alt (string "the ")
       (string "a ")))
(define noun
  (alt (string "student ")
       (string "professor ")))
(define verb
  (alt (string "studies ")
       (string "lectures ")))
(define noun-phrase
  (seq article noun))
(define verb-phrase
  (seq verb noun-phrase))
(define sentence
  (seq noun-phrase verb-phrase))