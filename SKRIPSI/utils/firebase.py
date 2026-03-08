"""utils/firebase.py - Simple Firebase Realtime Database helper.

This module wraps the minimum required functionality to push and pull
schedule (jadwal) data from a Firebase project.  You will need to create
a Firebase project, enable the Realtime Database (or Firestore with the
same patterns), then download a service account JSON file and supply the
URL for your database.

Usage example (e.g. in your main startup code):

    import utils.firebase as fb
    fb.init('path/to/serviceAccountKey.json', 'https://<your-db>.firebaseio.com')

Once initialized you can call the helpers directly or let
``utils.storage`` automatically delegate when ``USE_FIREBASE`` is set.

"""

import firebase_admin
from firebase_admin import credentials, db

_initialized = False
_db_ref = None


def init(service_account_path: str, database_url: str):
    """Initialize the Firebase Admin SDK with a service account.

    The database_url should point to the Realtime Database endpoint for
    your project (e.g. ``https://project-id.firebaseio.com``).
    """
    global _initialized, _db_ref
    if _initialized:
        return
    cred = credentials.Certificate(service_account_path)
    firebase_admin.initialize_app(cred, {'databaseURL': database_url})
    _db_ref = db.reference('/')
    _initialized = True


def _ensure():
    if not _initialized:
        raise RuntimeError('Firebase not initialized, call init() first')


def fetch_jadwal():
    """Return the list of jadwal items stored in the remote database.

    If the path does not exist, an empty list is returned.
    """
    _ensure()
    data = _db_ref.child('jadwal').get()
    return data or []


def store_jadwal(jadwal_list):
    """Overwrite the remote ``jadwal`` node with the given list.

    The list should be JSON-serializable (typically a list of dicts).
    """
    _ensure()
    _db_ref.child('jadwal').set(jadwal_list)


def delete_jadwal():
    """Remove the entire jadwal node from the database.
    """
    _ensure()
    _db_ref.child('jadwal').delete()


# alarm helpers ------------------------------------------------------------

def fetch_alarms():
    """Retrieve the list of alarms stored remotely.

    Only public alarms should be saved to the database, so callers can
    safely merge the returned list with whatever they keep locally.
    """
    _ensure()
    data = _db_ref.child('alarm').get()
    return data or []


def store_alarms(alarm_list):
    """Overwrite the remote ``alarm`` node with the given list.

    Typically this list will contain only alarms whose ``public`` key is
    ``True``.  The caller is responsible for filtering.
    """
    _ensure()
    _db_ref.child('alarm').set(alarm_list)


def delete_alarms():
    """Remove the entire alarm node from the database.
    """
    _ensure()
    _db_ref.child('alarm').delete()
