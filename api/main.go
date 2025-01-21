package main

import (
	"encoding/json"
	"log"
	"net/http"
)

type Response struct {
	Message string `json:"message"`
}

// CORS Middleware
func enableCORS(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		// Set CORS headers
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")

		// Handle preflight requests
		if r.Method == "OPTIONS" {
			w.WriteHeader(http.StatusOK)
			return
		}

		next(w, r)
	}
}

func main() {
	// Define routes with CORS middleware
	http.HandleFunc("/api/v1", enableCORS(handleRequest))

	// Start server
	log.Println("Server starting on port 8080...")
	if err := http.ListenAndServe(":8080", nil); err != nil {
		log.Fatal(err)
	}
}

func handleRequest(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")

	log.Println("Request received:", r.Method, r.URL)

	switch r.Method {
	case http.MethodGet:
		json.NewEncoder(w).Encode(Response{Message: "GET /api/v1 endpoint"})

	case http.MethodPost:
		json.NewEncoder(w).Encode(Response{Message: "POST /api/v1 endpoint"})

	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}
