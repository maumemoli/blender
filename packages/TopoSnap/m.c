#include <stdio.h>
#include <omp.h>
#include <stdlib.h>
#include <time.h>
#include <stdbool.h>

int main() {
    // timer start
    clock_t start = clock();
    // Array of random numbers to search
    int size = 999999999;  // Size of the array
    int *arr = (int *)malloc(size * sizeof(int));
    if (arr == NULL) {
        fprintf(stderr, "Memory allocation failed\n");
        return 1;
    }

    bool use_multiple_threads = false;  // Set to false to use a single thread

    // Seed the random number generator with the current time
    srand(time(0));


    int target = 50;  // Element to find
    int count = 0;    // Counter to count occurrences of the target

    // Find number of available threads
    int max_threads = omp_get_max_threads();
    int num_threads = use_multiple_threads ? max_threads : 1;
    printf("Used Threads: %d\n", num_threads);

    // Parallelize the search using OpenMP
    if (!use_multiple_threads) {
        omp_set_num_threads(num_threads);  // Use a single thread
    }
    else {
        omp_set_num_threads(num_threads);  // Use all available threads
    }


    // Generate random integers and store them in the array
    #pragma omp parallel
    {
        unsigned int seed = time(NULL) ^ omp_get_thread_num();  // Seed for each thread
        #pragma omp for
        for (int i = 0; i < size; i++) {
            arr[i] = rand() % 100;  // Random integers between 0 and 99
        }
    }


    #pragma omp parallel for reduction(+:count)
    for (int i = 0; i < size; i++) {
        if (arr[i] == target) {
            count++;
        }
    }

    printf("Element %d found %d times\n", target, count);

    free(arr);
    // timer end
    clock_t end = clock();
    double time_spent = (double)(end - start) / CLOCKS_PER_SEC;
    printf("Time taken: %f seconds\n", time_spent);

    return 0;
}