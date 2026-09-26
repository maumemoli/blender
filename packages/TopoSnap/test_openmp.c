#include <stdio.h>
#include <pthread.h>

#define NUM_THREADS 4
#define NUM_ITERATIONS 10

void* thread_function(void* arg) {
    int thread_id = *(int*)arg;
    for (int i = thread_id; i < NUM_ITERATIONS; i += NUM_THREADS) {
        printf("Thread %d is working on iteration %d\n", thread_id, i);
    }
    return NULL;
}

__declspec(dllexport) void run_pthread() {
    pthread_t threads[NUM_THREADS];
    int thread_ids[NUM_THREADS];

    for (int i = 0; i < NUM_THREADS; i++) {
        thread_ids[i] = i;
        pthread_create(&threads[i], NULL, thread_function, &thread_ids[i]);
    }

    for (int i = 0; i < NUM_THREADS; i++) {
        pthread_join(threads[i], NULL);
    }
}