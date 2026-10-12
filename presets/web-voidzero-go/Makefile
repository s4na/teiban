PNPM ?= pnpm

.PHONY: install dev-web dev-api check fmt
install:
	cd web && $(PNPM) install --frozen-lockfile
dev-web:
	cd web && $(PNPM) run dev
dev-api:
	cd api && go run ./cmd/server
check:
	cd web && $(PNPM) run check
	cd web && $(PNPM) run lint:css
	cd web && $(PNPM) test
	cd web && $(PNPM) run build
	cd api && test -z "$$(gofmt -l .)"
	cd api && go vet ./...
	cd api && golangci-lint run
	cd api && go test -race ./...
	cd api && go build ./...
fmt:
	cd web && $(PNPM) run fmt
	cd api && gofmt -w .
