PNPM ?= pnpm

.PHONY: install dev-web dev-api check fmt
install:
	$(PNPM) --dir web install --frozen-lockfile
dev-web:
	$(PNPM) --dir web run dev
dev-api:
	cd api && go run ./cmd/server
check:
	$(PNPM) --dir web run check
	$(PNPM) --dir web run lint:css
	$(PNPM) --dir web test
	$(PNPM) --dir web run build
	cd api && test -z "$$(gofmt -l .)"
	cd api && go vet ./...
	cd api && golangci-lint run
	cd api && go test -race ./...
	cd api && go build ./...
fmt:
	$(PNPM) --dir web run fmt
	cd api && gofmt -w .
