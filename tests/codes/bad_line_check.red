;; Blank lines are part of the test
ADD  #4   -1
MOV  #0   @-2
JMP       -2
ADD  #4   -1

MOV  #0   @-2
JMP       -2


ADD  ~4   -1
MOV  #0   @-2
JMP       -2
;; commented
ADD  #4   -1
XYZ  #0   @-2

