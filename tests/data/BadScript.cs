using UnityEngine;
using System.Collections;

public class BadPerformanceScript : MonoBehaviour {

    void Start () {
    
    }
    
    // Update is called once per frame
    void Update () {
        // BAD: GetComponent in Update
        Rigidbody rb = GetComponent<Rigidbody>();
        rb.AddForce(Vector3.up);
        
        // BAD: Find in Update
        GameObject player = GameObject.Find("Player");
        
        // BAD: Debug.Log in Update
        Debug.Log("Updating...");
        
        // BAD: New string in Update
        string s = new string('a', 100);
    }
}
