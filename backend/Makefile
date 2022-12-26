# This is the default target, which will be built when 
# you invoke make
.PHONY: all
all: backend

# This rule tells make how to build backend from main.c
backend:
	mkdir -p ./out
	gcc -o ./out/backend ./src/main.c 

# This rule tells make to delete backend and backend.o
.PHONY: clean 
clean:
	rm -rf out
