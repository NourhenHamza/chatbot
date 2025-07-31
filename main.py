from app import app
import webbrowser
import threading
import time

def open_browser():
    """Ouvre le navigateur après un délai pour laisser le serveur démarrer"""
    time.sleep(2)  # Attendre 2 secondes pour que le serveur démarre
    webbrowser.open('http://127.0.0.1:5000')

if __name__ == "__main__":
    # Lancer l'ouverture du navigateur dans un thread séparé
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # Lancer l'application Flask
    app.run(debug=True, host='0.0.0.0', use_reloader=False)

