tracecatd: llist.o tracecatd.c
	gcc -Wall -Wextra llist.o tracecatd.c -o tracecatd

llist.o: includes/llist.h includes/llist.c
	gcc -Wall -Wextra -fPIC includes/llist.h -c includes/llist.c

clean:
	rm -rf *.o *.gch tracecatd
