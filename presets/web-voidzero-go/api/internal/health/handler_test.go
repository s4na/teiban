package health

import (
	"io"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestHealth(t *testing.T) {
	server := httptest.NewServer(Handler())
	defer server.Close()
	response, err := server.Client().Get(server.URL + "/api/health")
	if err != nil {
		t.Fatal(err)
	}
	defer func() {
		if err := response.Body.Close(); err != nil {
			t.Error(err)
		}
	}()
	body, err := io.ReadAll(response.Body)
	if err != nil {
		t.Fatal(err)
	}
	if response.StatusCode != http.StatusOK || string(body) != `{"ok":true}` || response.Header.Get("Content-Type") != "application/json" {
		t.Fatalf("unexpected response: %d %s", response.StatusCode, body)
	}
}

func TestRoutes(t *testing.T) {
	for _, tc := range []struct {
		method string
		path   string
		status int
	}{
		{http.MethodPost, "/api/health", http.StatusMethodNotAllowed},
		{http.MethodGet, "/missing", http.StatusNotFound},
	} {
		recorder := httptest.NewRecorder()
		Handler().ServeHTTP(recorder, httptest.NewRequest(tc.method, tc.path, nil))
		if recorder.Code != tc.status {
			t.Errorf("%s %s: got %d, want %d", tc.method, tc.path, recorder.Code, tc.status)
		}
	}
}
