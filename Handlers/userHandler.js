const { initializeApp } = require('firebase/app');
const { getFirestore, collection, setDoc, addDoc, doc, getDoc, updateDoc } = require('firebase/firestore');
const { getAuth, createUserWithEmailAndPassword, signInWithEmailAndPassword, sendPasswordResetEmail } = require('firebase/auth');

const firebaseConfig = {
  // Firebase configuration
  apiKey: "AIzaSyAcS2sMgKIKbIVAwTs229eoQWaFCWxZd9o",
  authDomain: "agro-vision-403510.firebaseapp.com",
  projectId: "agro-vision-403510",
  storageBucket: "agro-vision-403510.appspot.com",
  messagingSenderId: "623850716036",
  appId: "1:623850716036:web:74a7812417e572bb757bd1"
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);

const signupRequest = (request, response) => {
  const { emailField, fullnameField, passwordField } = request.body;

  if (!emailField || !fullnameField || !passwordField) {
    return response.status(400).json({
      status: 'fail',
      message: 'All fields need to be filled. (Email, Full name, and Password)',
    });
  }

  createUserWithEmailAndPassword(auth, emailField, passwordField)
    .then((userCred) => {
      console.log(userCred.user);
      const email = emailField;
      const name = fullnameField;
      const password = passwordField;

      const userFirebaseID = userCred.user.uid;
      
      const accountsCollection = doc(collection(db, 'accounts'), userFirebaseID); //menambah penamaan berdasarkan uid dari firebase auth
      setDoc(accountsCollection, { email, name, password })
        .then((docRef) => {
          console.log('Document written with ID: ', userFirebaseID);
          return response.status(201).json({
            status: 'success',
            message: 'Sign-up has been successful',
            data : {
              uid: userFirebaseID,
            }
          });
        })
        .catch((error) => {
          console.error('Error writing document:', error);
          return response.status(500).json({
            status: 'fail',
            message: 'An error occurred during sign-up',
          });
        });
    })
    .catch((error) => {
      console.error('Error creating user:', error);
      return response.status(500).json({
        status: 'fail',
        message: 'An error occurred during sign-up',
      });
    });
};

const signinRequest = (request, response) => {
  const { email, password } = request.body;

  if (!email || !password) {
    return response.status(400).json({
      status: 'fail',
      message: 'Email and password are required.',
    });
  }

  signInWithEmailAndPassword(auth, email, password)
    .then((userCred) => {
      console.log(userCred.user);
      return response.status(200).json({
        status: 'success',
        message: 'Sign-in successful',
        data: {
          uid: userCred.user.uid,
          email: userCred.user.email
        },
      });
    })
    .catch((error) => {
      console.error('Error signing in:', error);
      return response.status(500).json({
        status: 'fail',
        message: 'An error occurred during sign-in',
      });
    });
};

const signoutRequest = (request, response) => {
  auth.signOut()
    .then(() => {
      return response.status(200).json({
        status: 'success',
        message: 'Sign-out successful',
      });
    })
    .catch((error) => {
      console.error('Error signing out:', error);
      return response.status(500).json({
        status: 'fail',
        message: 'An error occurred during sign-out',
      });
    });
};

const getUserData = async (uid) => {
  try {
    const userDocRef = doc(db, 'accounts', uid);
    const userDocSnap = await getDoc(userDocRef);

    if (userDocSnap.exists()) {
      const userData = userDocSnap.data();
      return {
        status: 'Success',
        data: {
          uid: userData.uid,
          email: userData.email,
          name: userData.name,
          profilePicture: userData.profilePicture
        }
      };
    } else {
      return {
        status: 'Failed',
        message: 'Data not found'
      };
    }
  } catch (error) {
    console.error('Error retrieving user data:', error);
    return {
      status: 'Failed',
      message: 'Error retrieving user data'
    };
  }
};


const resetPasswordRequest = (req, res) => {
  const { email } = req.body;

  if (!email) {
    return res.status(400).json({
      status: 'fail',
      message: 'Email is required.'
    });
  }

  sendPasswordResetEmail(auth, email)
    .then(() => {
      return res.status(200).json({
        status: 'success',
        message: 'Password reset email sent successfully.'
      });
    })
    .catch((error) => {
      console.error('Error sending password reset email:', error);
      return res.status(500).json({
        status: 'fail',
        message: 'An error occurred while sending the password reset email.'
      });
    });
};

const editNameRequest = async (req, res) => {
  const { uid } = req.params;
  const { name } = req.body;
  
  if (!uid || !name) {
    return res.status(400).json({
      status: 'fail',
      message: 'UID and name are required.'
    });
  }

  try {
    const userRef = doc(db, 'accounts', uid);
    const userDoc = await getDoc(userRef);

    if (!userDoc.exists()) {
      return res.status(404).json({
        status: 'fail',
        message: 'User not found.'
      });
    }

    await updateDoc(userRef, { name });

    return res.status(200).json({
      status: 'success',
      message: 'Name updated successfully.'
    });
  } catch (error) {
    console.error('Error updating name:', error);
    return res.status(500).json({
      status: 'fail',
      message: 'An error occurred while updating name.'
    });
  }
};

const addProfilePicture = async (req, res) => {
  const { uid } = req.params;
  const { profilePicture } = req.body;

  if (!uid || !profilePicture) {
    return res.status(400).json({
      status: 'fail',
      message: 'UID and profile picture are required.'
    });
  }

  try {
    const userRef = doc(db, 'accounts', uid);
    const userDoc = await getDoc(userRef);

    if (!userDoc.exists()) {
      return res.status(404).json({
        status: 'fail',
        message: 'User not found.'
      });
    }

    await updateDoc(userRef, { profilePicture });

    return res.status(200).json({
      status: 'success',
      message: 'Profile picture added successfully.'
    });
  } catch (error) {
    console.error('Error adding profile picture:', error);
    return res.status(500).json({
      status: 'fail',
      message: 'An error occurred while adding profile picture.'
    });
  }
};
module.exports = {
  signupRequest,
  signinRequest,
  signoutRequest,
  getUserData,
  resetPasswordRequest,
  editNameRequest,
  addProfilePicture
};
