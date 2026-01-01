#include <stdio.h>
#include <stdlib.h>
#include <mpi.h>
#include <math.h>
#include <time.h>

int main(int argc, char *argv[]) {
    int rank, size;
    long long int local_points, i;
    long long int local_hits = 0, global_hits = 0;
    long long int total_points;
    double x, y;
    double local_pi, global_pi;
    unsigned int seed;

    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    if (rank == 0) {
        if (argc != 2) {
            fprintf(stderr, "Usage: %s <total_points>\n", argv[0]);
            MPI_Abort(MPI_COMM_WORLD, 1);
        }
        total_points = atoll(argv[1]);
    }

    /* Broadcast total number of points to all ranks */
    MPI_Bcast(&total_points, 1, MPI_LONG_LONG_INT, 0, MPI_COMM_WORLD);

    /* Divide work among ranks (last rank may do a bit more) */
    local_points = total_points / size;
    long long int remainder = total_points % size;
    if (rank < remainder) {
        local_points++;
    }

    /* Seed RNG differently on each rank */
    seed = (unsigned int) time(NULL) + (unsigned int) rank * 1337U;

    for (i = 0; i < local_points; i++) {
        x = (double) rand_r(&seed) / (double) RAND_MAX;
        y = (double) rand_r(&seed) / (double) RAND_MAX;
        if (x * x + y * y <= 1.0) {
            local_hits++;
        }
    }

    /* Reduce hits to rank 0 */
    MPI_Reduce(&local_hits, &global_hits, 1, MPI_LONG_LONG_INT,
               MPI_SUM, 0, MPI_COMM_WORLD);

    if (rank == 0) {
        global_pi = 4.0 * (double) global_hits / (double) total_points;
        printf("Total points     : %lld\n", total_points);
        printf("Points in circle : %lld\n", global_hits);
        printf("Estimated pi     : %.12f\n", global_pi);
    }

    MPI_Finalize();
    return 0;
}
