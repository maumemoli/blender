#include <stdlib.h>
#include <stdio.h>  // Include this for printf
#include <time.h>   // Include this for time_t and time
#include <stdbool.h> // Include this for bool



// Define a struct to hold the edges
typedef struct {
    int start;
    int end;
    int face_index;
    int twin_face_index; 
} Edge;

typedef struct {
    Edge* edges_array;
    int size;
} Edges;

typedef struct {
    int* loop_array;
    int size;
    int loop_offset;
    int face_index;
    Edges* edges;
} FaceLoop;

typedef struct {
    FaceLoop* array;
    int size;
} FaceLoops;

typedef struct {
    int* array;
    int size;
} DynamicArray;


// Struct to handle the data coming from Blender
typedef struct {
    int *face_loops;
    int *face_loops_start;
    int *face_loops_total;
    int faces_count;
} FaceLoopsData;

typedef struct {
    FaceLoops* face_loops;
    Edges* edges;
    
} MeshData;

// Declaring functions
FaceLoop extract_face_loop(FaceLoopsData Face_loops_data, int face_index);
void reorder_topology(int* face_loops, int* face_loops_start, int* face_loops_total, int faces_count, int starting_face, int edge_offset);
void offset_face_loop(FaceLoop face_loop, int offset);
Edges get_edges(FaceLoop face_loop);
void reverse_edges(Edge* edges, int length);
DynamicArray get_edge_connected_faceLoops(FaceLoopsData Face_loops_data, Edge edge);
FaceLoops get_edges_connected_faceLoops(FaceLoopsData Face_loops_data, Edges edges);
void free_face_loop(FaceLoop* face_loop);
FaceLoops get_face_connected_faceLoops(FaceLoopsData Face_loops_data, int face_index, int edge_offset);
bool is_in_array(int *array, int size, int element);
bool is_in_dynamic_array(DynamicArray* dynamic_array, int element);
void print_edges(Edges* edges);
void free_dynamic_array(DynamicArray* dynamic_array);
void free_face_loops(FaceLoops* face_loops);
void free_edges(Edges* edges);
void dynamic_array_append(DynamicArray* dynamic_array, int element);
void face_loops_append(FaceLoops* face_loops, FaceLoop face_loop);
void edges_append(Edges* edges, Edge edge);
void clearScreen();
void free_mesh_data(MeshData* mesh_data);
// Done declaring functions

void free_mesh_data(MeshData* mesh_data){
    free_face_loops(mesh_data->face_loops);
    free_edges(mesh_data->edges);
    free(mesh_data->face_loops);
    free(mesh_data->edges);
}

void clearScreen() {
#ifdef _WIN32
    system("cls");   // Windows
#else
    system("clear"); // Linux or macOS
#endif
}



bool is_in_dynamic_array(DynamicArray* dynamic_array, int element) {
    for (int i = 0; i < dynamic_array->size; i++) {
        if (dynamic_array->array[i] == element) {
            return true;  // Element found
        }
    }
    return false;  // Element not found
}

void free_edges(Edges* edges) {
    if (edges != NULL) {
        free(edges->edges_array);
        edges->edges_array = NULL; // Optional: Set to NULL to avoid dangling pointer
        // Remove the line `free(edges);` unless `edges->edges_array` was dynamically allocated
    }
}

void edges_append(Edges* edges, Edge edge){
    int current_size = edges->size;
    Edge* temp = (Edge*)realloc(edges->edges_array, (current_size + 1) * sizeof(Edge));
    if (temp == NULL) {
        fprintf(stderr, "Memory allocation failed\n");
        return;
    }
    edges->edges_array = temp;
    edges->edges_array[current_size] = edge;
    edges->size = current_size + 1;
}

void face_loops_append(FaceLoops* face_loops, FaceLoop face_loop){
    face_loops->size++;
    face_loops->array = (FaceLoop*)realloc(face_loops->array, face_loops->size * sizeof(FaceLoop));
    if (face_loops->array == NULL) {
        fprintf(stderr, "Memory allocation failed\n");
        return;
    }

    // Allocate memory for the new face loop's loop_array
    face_loops->array[face_loops->size - 1].loop_array = (int*)malloc(face_loop.size * sizeof(int));
    if (face_loops->array[face_loops->size - 1].loop_array == NULL) {
        fprintf(stderr, "Memory allocation failed\n");
        return;
    }

    // Copy the contents of the loop_array
    for (int i = 0; i < face_loop.size; i++) {
        face_loops->array[face_loops->size - 1].loop_array[i] = face_loop.loop_array[i];
    }

    // Copy the other fields
    face_loops->array[face_loops->size - 1].size = face_loop.size;
    face_loops->array[face_loops->size - 1].face_index = face_loop.face_index;
    face_loops->array[face_loops->size - 1].loop_offset = face_loop.loop_offset;
}

void dynamic_array_append(DynamicArray* dynamic_array, int element){
    int current_size = dynamic_array->size;
    int* temp = (int*)realloc(dynamic_array->array, (current_size + 1) * sizeof(int));
    if (temp == NULL) {
        fprintf(stderr, "Memory allocation failed\n");
        return;
    }
    dynamic_array->array = temp;
    dynamic_array->array[current_size] = element;
    dynamic_array->size = current_size + 1;
}


void free_face_loops(FaceLoops* face_loops) {
    if (face_loops != NULL) {
        for (int i = 0; i < face_loops->size; i++) {
            free_face_loop(&face_loops->array[i]);
        }
        free(face_loops->array);
        face_loops->array = NULL; // Optional: Set to NULL to avoid dangling pointer
        // Remove the line `free(face_loops->array);` unless `face_loops->array` was dynamically allocated
        free_edges(face_loops->array->edges);
    }
}


void free_dynamic_array(DynamicArray* dynamic_array) {
    if (dynamic_array != NULL) {
        free(dynamic_array->array);
        dynamic_array->array = NULL; // Optional: Set to NULL to avoid dangling pointer
        // Remove the line `free(dynamic_array->array);` unless `dynamic_array->array` was dynamically allocated
    }
}

// Function to check if an element is in the array
bool is_in_array(int *array, int size, int element) {
    for (int i = 0; i < size; i++) {
        if (array[i] == element) {
            return true;  // Element found
        }
    }
    return false;  // Element not found
}

FaceLoops get_face_connected_faceLoops(FaceLoopsData Face_loops_data, int face_index, int edge_offset) {
    // Initialize dynamic_array
    FaceLoop face_loop = extract_face_loop(Face_loops_data, face_index);
    face_loop.loop_offset = edge_offset;
    Edges edges = get_edges(face_loop);
    edges.size = face_loop.size;
    FaceLoops connected_face_loops = get_edges_connected_faceLoops(Face_loops_data, edges); 
    return connected_face_loops;
    


}

FaceLoops get_edges_connected_faceLoops(FaceLoopsData Face_loops_data, Edges edges) {
    FaceLoops connected_face_loops = {NULL, 0}; // Initialize dynamic_array
    DynamicArray related_edges = {NULL, 0}; // Initialize dynamic_array
    DynamicArray face_loops_ids = {NULL, 0}; // Initialize dynamic_array
    DynamicArray face_loops_offset = {NULL, 0}; // Initialize dynamic_array
    for (int i = 0; i < Face_loops_data.faces_count; i++){ // Loop through the face loops
        FaceLoop face_loop = extract_face_loop(Face_loops_data, i);
        for (int j=0; j < edges.size; j++){ // Loop through the edges
            for (int k=0; k < face_loop.size; k++){ // Offset face loop t
                offset_face_loop(face_loop, k);
                if (edges.edges_array[j].end == face_loop.loop_array[0] && edges.edges_array[j].start == face_loop.loop_array[1]){
                    dynamic_array_append(&related_edges, j);
                    dynamic_array_append(&face_loops_ids, i);
                    dynamic_array_append(&face_loops_offset, k);
                    break;
                }
            }
        }
        free_face_loop(&face_loop);
    }
    //let's sort the connected_face_loops in edges order
    for ( int i=0; i < edges.size; i++){
        for (int j=0; j < related_edges.size; j++){
            if (related_edges.array[j] == i){
                //let's append a copy of the face loop to the connected_face_loops
                FaceLoop face_loop = extract_face_loop(Face_loops_data, face_loops_ids.array[j]);
                offset_face_loop(face_loop, face_loops_offset.array[j]);
                face_loops_append(&connected_face_loops, face_loop);
            }
        }
    }
    free_dynamic_array(&related_edges);
    return connected_face_loops;
}



DynamicArray get_edge_connected_faceLoops(FaceLoopsData Face_loops_data, Edge edge) {
    DynamicArray dynamic_array = {NULL, 0}; // Initialize dynamic_array
    // Let's create a dynamic array to hold the face loops
    int current_size = 0;
    // Adding the first one
    int* connected_face_loops = NULL;
    for (int i = 0; i < Face_loops_data.faces_count; i++) {
        FaceLoop face_loop = extract_face_loop(Face_loops_data, i);
        Edges edges = get_edges(face_loop);
        edges.size = face_loop.size;
        if (edges.edges_array == NULL) {
            free_face_loop(&face_loop);
            free_edges(&edges);
            continue;
        }
        bool found = false;
        for (int j = 0; j < face_loop.size; j++) {
            if ((edges.edges_array[j].start == edge.end && edges.edges_array[j].end == edge.start)) {
                // Let's add the face loop to the list of face loops
                current_size++;
                int* temp = (int*)realloc(connected_face_loops, current_size * sizeof(int));
                if (temp == NULL) {
                    fprintf(stderr, "Memory allocation failed\n");
                    free_edges(&edges);
                    free(connected_face_loops); // Free previously allocated memory
                    return dynamic_array;
                }
                connected_face_loops = temp;
                connected_face_loops[current_size - 1] = i;
                found = true;
                break; // Exit the inner loop once the edge is found
            }
        }
        free_edges(&edges);
        free_face_loop(&face_loop);
    }
    dynamic_array.array = connected_face_loops;
    dynamic_array.size = current_size;
    return dynamic_array;
}

void print_edges(Edges* edges) {
    for (int i = 0; i < edges->size; i++) {
        printf("(%d, %d) ", edges->edges_array[i].start, edges->edges_array[i].end);
    }
    printf("\n");
}

// Function to get the edges from the face loop
Edges get_edges(FaceLoop face_loop) {
    Edges edges = {NULL, 0}; // Initialize edges

    for (int i = 0; i < face_loop.size; i++) {
        Edge edge = {face_loop.loop_array[i], face_loop.loop_array[(i + 1) % face_loop.size]};
        edges_append(&edges, edge);
    }

    return edges;
}

// Function to reverse the edges
void reverse_edges(Edge* edges, int length) {
    for (int i = 0; i < length; i++) {
        int temp = edges[i].start;
        edges[i].start = edges[i].end;
        edges[i].end = temp;
    }
}

// Function to offset the face loop
// [1, 2, 3, 4, 5] -> offset 2 -> [3, 4, 5, 1, 2]
void offset_face_loop(FaceLoop face_loop, int offset) {
    // Create a temporary array to hold the reordered values
    int* temp_array = (int*)malloc(face_loop.size * sizeof(int));
    if (temp_array == NULL) {
        //fprintf(stderr, "Memory allocation failed\n");
        return;
    }
    
    // Fill temp_array with the offset values
    for (int i = 0; i < face_loop.size; i++) {
        temp_array[(i + offset) % face_loop.size] = face_loop.loop_array[i];
    }

    // Copy the values from temp_array back to loop_array
    for (int i = 0; i < face_loop.size; i++) {
        face_loop.loop_array[i] = temp_array[i];
    }

    face_loop.loop_offset = offset;
    free(temp_array);  // Don't forget to free the temporary array
}

// Function to free the dynamically allocated memory for the loop_array
void free_face_loop(FaceLoop* face_loop) {
    if (face_loop != NULL) {
        free(face_loop->loop_array);
        face_loop->loop_array = NULL; // Optional: Set to NULL to avoid dangling pointer
        // Remove the line `free(face_loop);` unless `face_loop` was dynamically allocated
    }
}

// Function to extract a face loop from the face loops struct
FaceLoop extract_face_loop(FaceLoopsData Face_loops_data, int face_index) {
    int start = Face_loops_data.face_loops_start[face_index];
    int end = start + Face_loops_data.face_loops_total[face_index];
    int length = end - start;

    FaceLoop face_loop;
    face_loop.size = length;
    face_loop.loop_offset = 0;
    face_loop.loop_array = (int*)malloc(length * sizeof(int));
    if (face_loop.loop_array == NULL) {
        fprintf(stderr, "Memory allocation failed\n");
        return face_loop;
    }

    for (int i = 0; i < length; i++) {
        face_loop.loop_array[i] = Face_loops_data.face_loops[start + i];
    }
    face_loop.face_index = face_index;

    return face_loop;
}




// Reorder the topology by providing the face loops, face loops start, face loops total, face loops count, starting face, and edge offset
void reorder_topology(int* face_loops, int* face_loops_start, int* face_loops_total, int faces_count, int starting_face, int edge_offset) {
    clearScreen();
    FaceLoopsData face_loops_data = {face_loops, face_loops_start, face_loops_total, faces_count};
    // get the starting face loop
    FaceLoop starting_face_loop = extract_face_loop(face_loops_data, starting_face);
    // offset the face loop
    offset_face_loop(starting_face_loop, edge_offset);
    DynamicArray parsed_face_idxs = {NULL, 0}; // Initialize dynamic_array
    FaceLoops reordered_face_loops = {NULL, 0}; // Initialize dynamic_array
    face_loops_append(&reordered_face_loops, starting_face_loop);

    FaceLoops contiguous_face_loops = {NULL, 0};
    face_loops_append(&contiguous_face_loops, starting_face_loop);

    dynamic_array_append(&parsed_face_idxs, starting_face_loop.face_index);
    free_face_loop(&starting_face_loop);
    bool no_more_face_loops = false;
    while (!no_more_face_loops){
        
        // getting the connected faces to the last face loop
        FaceLoops temp = {NULL, 0};// this is the next contiguous face loops
        for (int i =0; i < contiguous_face_loops.size; ++i)
        {
            FaceLoops connected_face_loops = get_face_connected_faceLoops(face_loops_data, contiguous_face_loops.array[i].face_index, contiguous_face_loops.array[i].loop_offset);
            for (int j = 0; j < connected_face_loops.size; j++){
                if (!is_in_dynamic_array(&parsed_face_idxs, connected_face_loops.array[j].face_index)){

                    face_loops_append(&temp,  connected_face_loops.array[j]);
                    face_loops_append(&reordered_face_loops, connected_face_loops.array[j]);
                    dynamic_array_append(&parsed_face_idxs, connected_face_loops.array[j].face_index);

                }
            }
            free_face_loops(&connected_face_loops);
        }
        free_face_loops(&contiguous_face_loops);
        if (temp.size == 0){
            no_more_face_loops = true;
            break;
        }
        contiguous_face_loops = temp;
        }
    printf("Reordered face loops size is %d\n", reordered_face_loops.size);
    printf("#######################\n");
    // let's print the reordered face loops
    for (int i = 0; i < reordered_face_loops.size; i++){
        printf("Face index: %d, Loop offset: %d, Loop: [ ", reordered_face_loops.array[i].face_index, reordered_face_loops.array[i].loop_offset);
        for (int j = 0; j < reordered_face_loops.array[i].size; j++){
            printf("%d ", reordered_face_loops.array[i].loop_array[j]);
        }
        printf("]\n");
    }

    // Free dynamically allocated memory
    free_face_loops(&reordered_face_loops);
    free_dynamic_array(&parsed_face_idxs);



    
}
// To compile: gcc -c -o my_c_lib.o my_c_lib.c 
// To create shared library: gcc -shared -o my_c_lib.dll my_c_lib.o
