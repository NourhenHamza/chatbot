// Variables globales
const messagesContainer = document.getElementById("messages")
const questionInput = document.getElementById("questionInput")
const sendButton = document.getElementById("sendButton")
const loading = document.getElementById("loading")
const status = document.getElementById("status")

// Compteur de messages pour l'historique
let messageCount = 0

/**
 * Ajouter un message au chat
 */
function addMessage(content, isUser = false, isInfo = false) {
  const messageDiv = document.createElement("div")
  messageDiv.className = `message ${isUser ? "user-message" : "bot-message"}${isInfo ? " info" : ""}`
  messageDiv.textContent = content
  messagesContainer.appendChild(messageDiv)
  messagesContainer.scrollTop = messagesContainer.scrollHeight
  messageCount++
}

/**
 * Gérer l'état de chargement
 */
function setLoading(isLoading) {
  loading.style.display = isLoading ? "block" : "none"
  sendButton.disabled = isLoading
  sendButton.textContent = isLoading ? "Envoi..." : "Envoyer"
  questionInput.disabled = isLoading

  if (isLoading) {
    questionInput.style.opacity = "0.6"
  } else {
    questionInput.style.opacity = "1"
    questionInput.focus() // Remettre le focus après la réponse
  }
}

/**
 * Définir une question dans l'input
 */
function setQuestion(question) {
  questionInput.value = question
  questionInput.focus()
}

/**
 * Gérer la touche Entrée
 */
function handleKeyPress(event) {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault()
    sendQuestion()
  }
}

/**
 * Envoyer une question à l'API
 */
async function sendQuestion() {
  const question = questionInput.value.trim()

  if (!question) {
    alert("Veuillez saisir une question")
    questionInput.focus()
    return
  }

  // Ajouter la question de l'utilisateur
  addMessage(question, true)
  questionInput.value = ""
  setLoading(true)

  try {
    const response = await fetch("/ask", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        question: question,
        use_mock_data: false,
      }),
    })

    if (!response.ok) {
      throw new Error(`Erreur HTTP: ${response.status}`)
    }

    const data = await response.json()

    if (data.error) {
      addMessage(`❌ Erreur: ${data.error}`)
    } else {
      // Afficher seulement la réponse principale
      addMessage(data.response || "Réponse reçue")
    }

    // Mettre à jour le statut de connexion
    updateConnectionStatus(true)
  } catch (error) {
    console.error("Erreur:", error)
    addMessage(`❌ Erreur de connexion: ${error.message}`)
    updateConnectionStatus(false, error.message)
  } finally {
    setLoading(false)
  }
}

/**
 * Mettre à jour le statut de connexion
 */
function updateConnectionStatus(isConnected, errorMessage = "") {
  if (isConnected) {
    status.textContent = "✅ Connecté au serveur Flask"
    status.className = "status"
  } else {
    status.textContent = `❌ Erreur de connexion: ${errorMessage}`
    status.className = "status error"
  }
}

/**
 * Effacer le chat
 */
function clearChat() {
  if (confirm("Êtes-vous sûr de vouloir effacer tout le chat ?")) {
    messagesContainer.innerHTML = `
            <div class="message bot-message">
                👋 Chat effacé ! Je suis prêt pour de nouvelles questions.
            </div>
        `
    messageCount = 1
    questionInput.focus()
  }
}

/**
 * Afficher les collections disponibles
 */
async function showCollections() {
  setLoading(true)

  try {
    const response = await fetch("/collections")

    if (!response.ok) {
      throw new Error(`Erreur HTTP: ${response.status}`)
    }

    const data = await response.json()

    if (data.error) {
      addMessage(`❌ Erreur lors de la récupération des collections: ${data.error}`)
    } else if (data.collections && data.collections.length > 0) {
      addMessage("📚 Collections disponibles dans la base de données:")

      data.collections.forEach((collection) => {
        const info = `• ${collection.display_name || collection.name} (${collection.document_count || 0} documents)`
        addMessage(info, false, true)
      })

      addMessage("💡 Vous pouvez poser des questions sur ces collections !", false, true)
    } else {
      addMessage("ℹ️ Aucune collection trouvée dans la base de données.")
    }
  } catch (error) {
    console.error("Erreur:", error)
    addMessage(`❌ Erreur lors de la récupération des collections: ${error.message}`)
  } finally {
    setLoading(false)
  }
}

/**
 * Tester la connexion au serveur
 */
async function testConnection() {
  try {
    const response = await fetch("/health")

    if (response.ok) {
      const data = await response.json()
      updateConnectionStatus(true)

      if (data.collections_count) {
        addMessage(`📚 ${data.collections_count} collection(s) disponible(s) dans la base de données`)
      }

      // Afficher un message de bienvenue avec les collections
      if (data.collections && Object.keys(data.collections).length > 0) {
        const collectionNames = Object.keys(data.collections).join(", ")
        addMessage(`🗃️ Collections détectées: ${collectionNames}`, false, true)
      }
    } else {
      throw new Error("Serveur non accessible")
    }
  } catch (error) {
    updateConnectionStatus(false, "Impossible de se connecter au serveur Flask")
    addMessage("⚠️ Vérifiez que le serveur Flask est bien démarré sur le port 5000")
  }
}

/**
 * Ajouter des suggestions contextuelles
 */
function addContextualSuggestions() {
  const suggestions = [
    "Combien d'éléments y a-t-il dans chaque collection ?",
    "Peux-tu me donner un aperçu des données ?",
    "Quels sont les champs disponibles ?",
    "Montre-moi des exemples de données",
  ]

  const randomSuggestion = suggestions[Math.floor(Math.random() * suggestions.length)]

  setTimeout(() => {
    if (messageCount <= 3) {
      // Seulement si peu de messages
      addMessage(`💡 Suggestion: "${randomSuggestion}"`, false, true)
    }
  }, 3000)
}

/**
 * Initialisation au chargement de la page
 */
window.onload = () => {
  testConnection()
  questionInput.focus()

  // Ajouter des suggestions après un délai
  addContextualSuggestions()

  // Ajouter un gestionnaire pour le redimensionnement
  window.addEventListener("resize", () => {
    messagesContainer.scrollTop = messagesContainer.scrollHeight
  })
}

/**
 * Gestion des erreurs globales
 */
window.addEventListener("error", (event) => {
  console.error("Erreur JavaScript:", event.error)
  addMessage("⚠️ Une erreur inattendue s'est produite. Rechargez la page si nécessaire.")
})
