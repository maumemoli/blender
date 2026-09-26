#include <stdlib.h>
#include <stdio.h>  // Include this for printf
#include <time.h>   // Include this for time_t and time
#include <stdbool.h> // Include this for bool
#include <omp.h>
#include <string.h> // Include this for memset
// Define the enum for element types
typedef enum {
    EDGE,
    FACE_LOOP,
    INT
} ElementType;

// Define the Collection struct
typedef struct {
    void* array;
    int size;
    ElementType type;
} Collection;

// Define a struct to hold the edges
typedef struct {
    int index;
    int start;
    int end;
    int face_index;
    int twin_edge_index; 
} Edge;

typedef struct {
    Collection loops;
    int loop_offset;
    int face_index;
    Collection edges;
} FaceLoop;


// Struct to handle the data coming from Blender
typedef struct {
    int *face_loops;
    int *face_loops_start;
    int *face_loops_total;
    int faces_count;
} FaceLoopsData;

typedef struct {
    int *face_loops;
    int *face_loops_start;
    int *face_loops_total;
    int faces_count;
    int loops_count;
    Collection faces;
    Collection edges;
    
} MeshData;

// Function to initialize a Collection
Collection initialize_collection(ElementType type) {
    Collection collection;
    collection.array = NULL;
    collection.size = 0;
    collection.type = type;
    return collection;
}

// Function to append an element to a Collection
void collection_append(Collection* collection, void* element) {
    collection->size++;
    switch (collection->type) {
        case EDGE:
            collection->array = realloc(collection->array, collection->size * sizeof(Edge));
            if (collection->array == NULL) {
                fprintf(stderr, "Memory allocation failed\n");
                exit(EXIT_FAILURE);
            }
            ((Edge*)collection->array)[collection->size - 1] = *(Edge*)element;
            break;
        case FACE_LOOP:
            collection->array = realloc(collection->array, collection->size * sizeof(FaceLoop));
            if (collection->array == NULL) {
                fprintf(stderr, "Memory allocation failed\n");
                exit(EXIT_FAILURE);
            }
            ((FaceLoop*)collection->array)[collection->size - 1] = *(FaceLoop*)element;
            break;
        case INT:
            collection->array = realloc(collection->array, collection->size * sizeof(int));
            if (collection->array == NULL) {
                fprintf(stderr, "Memory allocation failed\n");
                exit(EXIT_FAILURE);
            }
            ((int*)collection->array)[collection->size - 1] = *(int*)element;
            break;
    }
}

// Declaring functions
FaceLoop extract_face_loop(MeshData Face_loops_data, int face_index);
void free_face_loop(FaceLoop* face_loop);
void free_mesh_data(MeshData* mesh_data);
void initialize_face_loops(MeshData* mesh_data);
MeshData initialize_mesh_data(FaceLoopsData faceloops_data);
void reorder_topology(int* face_loops, int* face_loops_start, int* face_loops_total, int faces_count, int starting_face, int edge_offset);
void print_face_loop(FaceLoop* face_loop, MeshData* mesh_data);
void print_edge(Edge* edge, MeshData* mesh_data, int indentation);
void clearScreen();
void offset_face_loop(FaceLoop* face_loop, int offset);


// Function to clear the screen
void clearScreen() {
#ifdef _WIN32
    system("cls");   // Windows
#else
    system("clear"); // Linux or macOS
#endif
}

void offset_face_loop(FaceLoop* face_loop, int offset) {
    face_loop->loop_offset = offset;
    int* temp_loops = malloc(face_loop->loops.size * sizeof(int));
    int* temp_edges = malloc(face_loop->edges.size * sizeof(int));
    if (temp_loops == NULL || temp_edges == NULL) {
        fprintf(stderr, "Memory allocation failed\n");
        exit(EXIT_FAILURE);
    }

    int loop_size = face_loop->loops.size;
    for (int i = 0; i < loop_size; i++) {
        // Offset the loop index and ensure it wraps around correctly
        int offset_index = (i + offset) % loop_size;
        printf("Offset index %d --> %d\n", i,offset_index);
        temp_loops[offset_index] = ((int*)face_loop->loops.array)[i];
        temp_edges[offset_index] = ((int*)face_loop->edges.array)[i];
    }

    // let's copy back the temp_loops to the loops
    for (int i = 0; i < loop_size; i++) {
        ((int*)face_loop->loops.array)[i] = temp_loops[i];
        ((int*)face_loop->edges.array)[i] = temp_edges[i];
    }
    // let's free the temp arrays
    free(temp_loops);
    free(temp_edges);
}

void print_face_loop(FaceLoop* face_loop, MeshData* mesh_data) {
    
    printf("====================================\n");
    printf("Face Index: %d\n", face_loop->face_index);
    printf("Loops Count: %d\n", face_loop->loops.size);
    printf("Loop Offset: %d\n", face_loop->loop_offset);
    printf("Loops: [");
    for (int i = 0; i < face_loop->loops.size; i++) {
        printf("%d ", ((int*)face_loop->loops.array)[i]);
    }
    printf("]\n");
    printf("Edges: \n");
    for (int i = 0; i < face_loop->edges.size; i++) {
        int edge_index = ((int*)face_loop->edges.array)[i];
        // get the pointer to the edge
        print_edge(&((Edge*)mesh_data->edges.array)[edge_index], mesh_data, 4);
    }
    printf("\n");
}


void print_edge(Edge* edge, MeshData* mesh_data, int indentation) {
    char* indent = malloc(indentation + 1);
    if (indent == NULL) {
        fprintf(stderr, "Memory allocation failed\n");
        exit(EXIT_FAILURE);
    }
    memset(indent, ' ', indentation);
    indent[indentation] = '\0';
    printf("%s==================EDGE ID %d==================\n", indent,edge->index);
    printf("%sStart/End: (%d, %d)\n", indent, edge->start, edge->end);
    printf("%sFace Index: %d\n", indent,edge->face_index);
    if (edge->twin_edge_index > 0)
    {
        printf("%sTwin Edge Index: %d\n",indent , edge->twin_edge_index);
        Edge* twin_edge = &((Edge*)mesh_data->edges.array)[edge->twin_edge_index];
        printf("%sStart/End: (%d, %d)\n", indent, twin_edge->start, twin_edge->end);
    }
    printf("%s==============================================\n", indent);
    free(indent);
}


// Done declaring functions

void free_mesh_data(MeshData* mesh_data) {
    if (mesh_data != NULL) {
        free(mesh_data->faces.array);
        free(mesh_data->edges.array);
        mesh_data->faces.array = NULL; // Optional: Set to NULL to avoid dangling pointer
        mesh_data->edges.array = NULL; // Optional: Set to NULL to avoid dangling pointer
        mesh_data->faces.size = 0;
        mesh_data->edges.size = 0;

        // Remove the line `free(mesh_data);` unless `mesh_data` was dynamically allocated
    }
}



// Function to free the dynamically allocated memory for the loop_array
void free_face_loop(FaceLoop* face_loop) {
    if (face_loop != NULL) {
        free(face_loop->loops.array);
        face_loop->loops.array = NULL; // Optional: Set to NULL to avoid dangling pointer
        // Remove the line `free(face_loop);` unless `face_loop` was dynamically allocated
    }
}

// Function to extract a face loop from the face loops struct
FaceLoop extract_face_loop(MeshData mesh_data, int face_index) {
    int start = mesh_data.face_loops_start[face_index];
    int end = start + mesh_data.face_loops_total[face_index];
    int length = end - start;

    FaceLoop face_loop;
    face_loop.loops = initialize_collection(INT);
    face_loop.edges = initialize_collection(INT);

    for (int i = 0; i < length; i++) {
        collection_append(&face_loop.loops, &mesh_data.face_loops[start + i]);
        int edge_index = start + i;
        collection_append(&face_loop.edges, &edge_index);
    }
    face_loop.face_index = face_index;
    face_loop.loop_offset = 0;
    
    return face_loop;

}

void find_twin_edge(MeshData* mesh_data, int edge_index, bool* parsed_edges) {
    Edge edge = ((Edge*)mesh_data->edges.array)[edge_index];
    int start = edge.start;
    int end = edge.end;
    int face_index = edge.face_index;
    edge.twin_edge_index = -1;
    for (int i = 0; i < mesh_data->edges.size; i++) {
        Edge twin_edge = ((Edge*)mesh_data->edges.array)[i];
        if (twin_edge.start == end && twin_edge.end == start && twin_edge.face_index != face_index) {
            edge.twin_edge_index = twin_edge.index;
            twin_edge.twin_edge_index = edge.index;
            ((Edge*)mesh_data->edges.array)[twin_edge.index] = twin_edge;
            parsed_edges[edge.index] = true;
            parsed_edges[twin_edge.index] = true;
            break;
            }
    
    }
    // free the edge and replace with the new edge
    ((Edge*)mesh_data->edges.array)[edge_index] = edge;
    
}

MeshData initialize_mesh_data(FaceLoopsData faceloops_data) {
    MeshData mesh_data;
    mesh_data.face_loops = faceloops_data.face_loops;
    mesh_data.face_loops_start = faceloops_data.face_loops_start;
    mesh_data.face_loops_total = faceloops_data.face_loops_total;
    mesh_data.faces_count = faceloops_data.faces_count;
    mesh_data.loops_count = 0;
    mesh_data.faces = initialize_collection(FACE_LOOP);
    mesh_data.edges = initialize_collection(EDGE);

    // let's figure out the number of loops by adding all the face_loops_total
    for (int i = 0; i < faceloops_data.faces_count; i++) {
        mesh_data.loops_count += faceloops_data.face_loops_total[i];
    }
    // let's initialize the edges

    int current_face_idx = 0;
    int next_loop = mesh_data.face_loops_total[0];

    // let's find the maximum threads we have available
    int max_threads = omp_get_max_threads();
    bool parallelize = true;
    if(!parallelize) max_threads = 1;

    printf("The max threads is %d\n", max_threads);
    // let's do the parallelization
    for (int i = 0; i < mesh_data.loops_count; i++) {
        int start = mesh_data.face_loops[i];
        int end = mesh_data.face_loops[i + 1];
        if (i == next_loop - 1) {
            int end_pos = mesh_data.face_loops_start[current_face_idx];
            end = mesh_data.face_loops[end_pos];
        }
        Edge* edge = (Edge*)malloc(sizeof(Edge));
        if (edge == NULL) {
            fprintf(stderr, "Memory allocation failed\n");
            exit(EXIT_FAILURE);
        }
        edge->index = i;
        edge->start = start;
        edge->end = end;
        edge->twin_edge_index = 0;
        collection_append(&mesh_data.edges, edge);
        if (i == next_loop || i == mesh_data.loops_count - 1) {
            // create faceloop
            FaceLoop face_loop = extract_face_loop(mesh_data, current_face_idx);
            collection_append(&mesh_data.faces, &face_loop);
        }
        if (i == next_loop) {
            current_face_idx++;
            next_loop = next_loop + mesh_data.face_loops_total[current_face_idx];
        }
        ((Edge*)mesh_data.edges.array)[i].face_index = current_face_idx;
        // print_edge(edge);
    }
    // let's find the twin edge
    bool* parsed_edges = (bool*)calloc(mesh_data.edges.size, sizeof(bool));
    if (parsed_edges == NULL) {
        fprintf(stderr, "Memory allocation failed\n");
        exit(EXIT_FAILURE);
    }
    memset(parsed_edges, 0, mesh_data.edges.size * sizeof(bool));

    int found_twin_edge_count = 0;
    #pragma omp parallel for num_threads(max_threads) reduction(+:found_twin_edge_count)
    for (int i = 0; i < mesh_data.edges.size; i++) {
        if (!parsed_edges[i]) {
            find_twin_edge(&mesh_data, i, parsed_edges);
            found_twin_edge_count++;
        }
    }
    // end of parallelization
    
    printf("The find twin edge count is %d\n", found_twin_edge_count);
    free(parsed_edges);
    return mesh_data;
}



// Reorder the topology by providing the face loops, face loops start, face loops total, face loops count, starting face, and edge offset
void reorder_topology(int* face_loops, int* face_loops_start, int* face_loops_total, int faces_count, int starting_face, int edge_offset) {
    printf("RT Face count is %d\n", faces_count);
    FaceLoopsData face_loops_data = {face_loops, face_loops_start, face_loops_total, faces_count};
    // get the starting face loop
    MeshData mesh_data = initialize_mesh_data(face_loops_data);
    int edges_number = mesh_data.edges.size;
    printf("The edge count is %d\n", edges_number);
    // let's print the edges
    bool print_log = true;
    if (print_log)
    {   
        printf("=========PRINTING EDGES==========\n");
        for (int i = 0; i < edges_number; i++){
            Edge edge = ((Edge*)mesh_data.edges.array)[i];
            print_edge(&edge, &mesh_data,0);
            }
        // // print face loops
        printf("=========PRINTING FACELOOPS==========\n");
        for (int i = 0; i < mesh_data.faces.size; i++) {
            FaceLoop face_loop = ((FaceLoop*)mesh_data.faces.array)[i];
            print_face_loop(&face_loop, &mesh_data);
            // offset_face_loop(&face_loop, 1);
            // print_face_loop(face_loop, mesh_data);
        }
    }

    printf("Freeing the mesh data\n");
    // free the mesh data
    free_mesh_data(&mesh_data);

}
// To compile: gcc -c -o my_c_lib.o toposnap_lib.c -fopenmp
// To create shared library: gcc -shared -o my_c_lib.dll my_c_lib.o -fopenmp