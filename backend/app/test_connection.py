import firebase_admin
from firebase_admin import firestore

try:
    print("🔄 Connecting to Firestore via Application Default Credentials...")
    
    # Initialize using your backend Project ID wrapper
    firebase_admin.initialize_app(options={
        'projectId': 'project-4fd7204c-297a-4c1b-b21'
    })
    
    db = firestore.client()
    
    # Write a quick data checkpoint document
    doc_ref = db.collection("test_connections").document("local_laptop_test")
    doc_ref.set({
        "status": "success",
        "message": "Local laptop workspace verified via gcloud CLI ADC!"
    })
    
    print("\n🔥 SUCCESS: Firestore connection verified!")

except Exception as e:
    print(f"\n❌ CONNECTION FAILED: {str(e)}")
