#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <time.h>
#include <unistd.h>
#include "includes/llist.h"

#define LINE_MAX_SIZE 255
#define METRICS_NAME_SIZE 64
#define OUTPUT_BUF_SIZE 4096
#define EXEC_SEPERATOR "___NeXt___"

enum metrics_type {
    NODES_METRICS,
    QUERY_METRICS
};

struct metrics_struct {
    char                name[METRICS_NAME_SIZE];
    enum metrics_type   type;
    llist               *nodes;
};

struct node_struct {
    FILE*               fd;
    char                data[LINE_MAX_SIZE];
};

llist* list_create()
{
    return llist_create(NULL);
}

int always_false(void* a, void* b)
{
    void* tmp;

    tmp = a;
    tmp = b;

    return -1;
}

void list_push_back(llist *list, void *data)
{
    llist_add_inorder(data, list, always_false);
}

char* get_metrics_type_str(enum metrics_type type)
{
    switch (type) {
        case NODES_METRICS:
            return "NODES";
        case QUERY_METRICS:
            return "QUERY";
    }

    return NULL;
}

void get_current_timestamp(char* buf)
{
    struct timespec tp;

    memset(&tp, 0, sizeof(tp));

    clock_gettime(CLOCK_BOOTTIME, &tp);

    sprintf(buf, "%ld%09ld", tp.tv_sec, tp.tv_nsec);
}

int main(int argc, char *argv[])
{
    if (argc < 5) {
    	printf("ERROR: Missing arguments.\n");
    	return 0;
    }

    char *conf_path = argv[1];
    char *data_path = argv[2];
    int period = atoi(argv[3]);
    int duration = atoi(argv[4]);

    FILE *conf_file;
    FILE *data_file;
    
    char line_buf[LINE_MAX_SIZE];
    char output_buf[OUTPUT_BUF_SIZE];

    struct metrics_struct *metrics = NULL;
    struct node_struct *node = NULL;
    llist *metrics_list = list_create();

    conf_file = fopen(conf_path, "r");

    while (1) {

        memset(line_buf, 0, sizeof(line_buf));

        if (!fgets(line_buf, LINE_MAX_SIZE, conf_file))
            break;

        line_buf[strcspn(line_buf, "\n")] = 0;
        line_buf[strcspn(line_buf, "\r")] = 0;

        if (line_buf[0] == 'N') {

            if (metrics)
                list_push_back(metrics_list, (void *)metrics);

            metrics = malloc(sizeof(struct metrics_struct));

            memset(metrics, 0, sizeof(struct metrics_struct));

            strncpy(metrics->name, &line_buf[7], METRICS_NAME_SIZE - 1);

            metrics->type = NODES_METRICS;

        } else if (line_buf[0] == 'Q') {

            if (metrics)
                list_push_back(metrics_list, (void *)metrics);

            metrics = malloc(sizeof(struct metrics_struct));

            memset(metrics, 0, sizeof(struct metrics_struct));

            strncpy(metrics->name, &line_buf[7], METRICS_NAME_SIZE - 1);

            metrics->type = QUERY_METRICS;

        } else if (line_buf[0] == ' ') {

            if (!metrics) {
                printf("ERROR: config format error.");
                return 0;
            }

            if (!metrics->nodes)
                metrics->nodes = list_create();

            node = malloc(sizeof(struct node_struct));

            memset(node, 0, sizeof(struct node_struct));

            strncpy(node->data, line_buf + strspn(line_buf, " \t"), LINE_MAX_SIZE);

            list_push_back(metrics->nodes, (void *)node);

        } else {
            printf("ERROR: config format error.");
            return 0;
        }
    }

    if (metrics) {
        list_push_back(metrics_list, (void *)metrics);
    } else {
        printf("Success!\n");
        return 0;
    }

    fclose(conf_file);

    data_file = fopen(data_path, "a");

    if (!data_file) {
        printf("ERROR: Data file create failed.\n");
        return 0;
    }

    struct node* p_metrics = NULL;

    double time_spent = 0;
    double time_sleep = 0;

    char curr_time[32];

    int now_time = (int)time(NULL);
    
    int end_time = now_time + duration;

    while (now_time <= end_time) {

        clock_t begin = clock();

        for (p_metrics = *metrics_list; p_metrics != NULL; p_metrics = p_metrics->next) {

            metrics = (struct metrics_struct*)p_metrics->data;

            get_current_timestamp(curr_time);

            fprintf(data_file, "%s: %s\n%s\n", get_metrics_type_str(metrics->type), metrics->name, curr_time);

            struct node* p_node = NULL;

            for (p_node = *metrics->nodes; p_node != NULL; p_node = p_node->next) {

                node = (struct node_struct*)p_node->data;

                if (!node->fd) {
                    node->fd = fopen(node->data, "r");
                    if (!node->fd) {
                        printf("ERROR: Node not found: %s.\n", node->data);
                        return 0;
                    }
                }

                memset(output_buf, 0, sizeof(output_buf));

                fread(output_buf, OUTPUT_BUF_SIZE, 1, node->fd);
                
                // some file node not support fseek
                if (!strlen(output_buf)) {
                    fclose(node->fd);
                    node->fd = fopen(node->data, "r");
                    fread(output_buf, OUTPUT_BUF_SIZE, 1, node->fd);
                }

                fseek(node->fd, 0, SEEK_SET);

                fprintf(data_file, "%s", output_buf);
            }

            fprintf(data_file, "%s\n", EXEC_SEPERATOR);
        }

        clock_t end = clock();

        time_spent = (double)(end - begin) / CLOCKS_PER_SEC * 1000; // ms

        time_sleep = ((double)period - time_spent) * 1000; // us

        if (time_sleep > 0)
            usleep((unsigned int)time_sleep);

        now_time = (int)time(NULL);
    }

    fclose(data_file);

    printf("Success!\n");

    return 0;
}