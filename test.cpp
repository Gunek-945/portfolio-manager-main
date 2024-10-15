#include <iostream>
using namespace std;

void circular_rotation(int x[], int size){
    int item_0= x[0];
    for (int j=1; j<size; j++)
        x[j-1]=x[j];
    x[size-1]=item_0;
}

void print_array(int x[], int size){
    for (int j = 0; j < size; j++) 
        cout << x[j] << '\t'; cout << endl;
}

int main(){
    int a[]= {1,2,3,4};
    // for (int i=0; i<4; i++)
    //     cout<<x[i]<<'\t';
    //for (int k=0; k<4; k++)
        circular_rotation(a, 4);
        print_array(a, 4);

    return 0;
}