/* llist.h
 * Generic Linked List
 */

struct node {
    void *data;
    struct node *next;
};

typedef struct node * llist;

/* llist_create: Create a linked list */
llist *llist_create(void *data);

/* llist_free: Free a linked list */
void llist_free(llist *list);

/* llist_add_inorder: Add to sorted linked list */
int llist_add_inorder(void *data, llist *list, 
                       int (*comp)(void *, void *));

/* llist_push: Add to head of list */
void llist_push(llist *list, void *data);

/* llist_pop: remove and return head of linked list */
void *llist_pop(llist *list);

/* llist_print: print linked list */
void llist_print(llist *list, void (*print)(void *data));
