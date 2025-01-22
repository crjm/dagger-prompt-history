package main

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	_ "github.com/mattn/go-sqlite3"
	"github.com/rs/zerolog/log"
)

type Message struct {
	Content string `json:"content"`
	Role    string `json:"role"`
}

type ModelResponseContent struct {
	Type  string `json:"type"`
	Text  string `json:"text,omitempty"`
	Image string `json:"image,omitempty"`
	// check if there are other types
}

type Event struct {
	ID                   int                    `json:"id"`
	SessionID            string                 `json:"session_id"`
	Messages             []Message              `json:"messages"`
	Response             []ModelResponseContent `json:"response"`
	Model                string                 `json:"model"`
	StopReason           string                 `json:"stop_reason"`
	Content              string                 `json:"content"`
	Type                 string                 `json:"type"`
	Role                 string                 `json:"role"`
	CacheReadInputTokens int                    `json:"cache_read_input_tokens"`
	InputTokens          int                    `json:"input_tokens"`
	OutputTokens         int                    `json:"output_tokens"`
}

var db *sql.DB

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
	log.Logger = log.With().Str("service", "api").Logger()
	// Initialize SQLite database
	var err error
	db, err = sql.Open("sqlite3", "./events.db")
	if err != nil {
		log.Fatal().Err(err).Msg("Failed to open database")
	}
	defer db.Close()

	// Create events table if it doesn't exist
	_, err = db.Exec(`
		CREATE TABLE IF NOT EXISTS events (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			session_id UUID NOT NULL,
			messages TEXT NOT NULL,
			response TEXT NOT NULL,
			model TEXT NOT NULL,
			stop_reason TEXT NOT NULL,
			content TEXT NOT NULL,
			type TEXT NOT NULL,
			role TEXT NOT NULL,
			cache_read_input_tokens INTEGER NOT NULL,
			input_tokens INTEGER NOT NULL,
			output_tokens INTEGER NOT NULL,
			created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
		)
	`)
	if err != nil {
		log.Fatal().Err(err).Msg("Failed to create events table")
	}

	// Define routes with CORS middleware
	http.HandleFunc("/api/v1", enableCORS(handlePostRequest))
	http.HandleFunc("/api/v1/events", enableCORS(handleGetRequest))

	// Start server
	log.Info().Msg("Server starting on port 8080...")
	if err := http.ListenAndServe(":8080", nil); err != nil {
		log.Fatal().Err(err).Msg("Failed to start server")
	}
}

func handleGetRequest(w http.ResponseWriter, r *http.Request) {
	log.Info().Str("method", r.Method).Str("url", r.URL.String()).Msg("Request received")
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	getEvents(w)
}

func handlePostRequest(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	w.Header().Set("Content-Type", "application/json")

	log.Info().Str("method", r.Method).Str("url", r.URL.String()).Msg("Request received")

	log.Info().Msg("POST /api/v1 endpoint")
	var event Event
	if err := json.NewDecoder(r.Body).Decode(&event); err != nil {
		log.Error().Err(err).Msg("Failed to decode request body")
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	log.Info().Str("messages", fmt.Sprintf("%+v", event.Messages)).Str("response", fmt.Sprintf("%+v", event.Response)).Msg(fmt.Sprintf("Event received: %+v", event))

	messages, err := json.Marshal(event.Messages)
	if err != nil {
		log.Error().Err(err).Msg("Failed to marshal user messages")
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	response, err := json.Marshal(event.Response)
	if err != nil {
		log.Error().Err(err).Msg("Failed to marshal model response")
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	// Insert event into database
	_, err = db.Exec("INSERT INTO events (session_id, messages, response, model, stop_reason, content, type, role, cache_read_input_tokens, input_tokens, output_tokens) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
		event.SessionID,
		string(messages),
		string(response),
		event.Model,
		event.StopReason,
		event.Content,
		event.Type,
		event.Role,
		event.CacheReadInputTokens,
		event.InputTokens,
		event.OutputTokens)
	if err != nil {
		log.Error().Err(err).Msg("Failed to insert event into database")
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	log.Info().Msg("Event stored successfully")
}

// get all events
func getEvents(w http.ResponseWriter) {
	rows, err := db.Query("SELECT * FROM events ORDER BY created_at DESC")
	if err != nil {
		log.Error().Err(err).Msg("Failed to get events")
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	var events []Event
	for rows.Next() {
		var event Event
		var messagesStr string
		var responseStr string
		var createdAt time.Time
		err := rows.Scan(
			&event.ID,
			&event.SessionID,
			&messagesStr,
			&responseStr,
			&event.Model,
			&event.StopReason,
			&event.Content,
			&event.Type,
			&event.Role,
			&event.CacheReadInputTokens,
			&event.InputTokens,
			&event.OutputTokens,
			&createdAt,
		)
		if err != nil {
			log.Error().Err(err).Msg("Failed to scan row")
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}

		// Parse the messages string into the Messages slice
		var messages []Message
		err = json.Unmarshal([]byte(messagesStr), &messages)
		if err != nil {
			log.Error().Err(err).Msg("Failed to unmarshal messages")
			continue
		}
		event.Messages = messages

		var response []ModelResponseContent
		err = json.Unmarshal([]byte(responseStr), &response)
		if err != nil {
			log.Error().Err(err).Msg("Failed to unmarshal model response")
			continue
		}
		event.Response = response

		events = append(events, event)
	}

	if err = rows.Err(); err != nil {
		log.Error().Err(err).Msg("Error iterating over rows")
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	log.Info().Msgf("Found %d events", len(events))

	json.NewEncoder(w).Encode(events)
}
