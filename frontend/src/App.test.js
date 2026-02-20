import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import App from "./App";

// mock useAuth hook
jest.mock("./AuthContext", () => ({
  useAuth: () => ({
    token: null,
    login: jest.fn(),
  }),
}));

// mock fetch
global.fetch = jest.fn();

beforeEach(() => {
  fetch.mockClear();
});

test("renders input page correctly", () => {
  render(<App />);

  expect(
    screen.getByPlaceholderText(/Type your medical question/i)
  ).toBeInTheDocument();

  expect(screen.getByText(/Send Message/i)).toBeInTheDocument();
});

test("send button disabled when no input", () => {
  render(<App />);

  const button = screen.getByRole("button", { name: /Send Message/i });
  expect(button).toBeDisabled();
});

test("send button enabled when text entered", async () => {
  render(<App />);

  const textarea = screen.getByPlaceholderText(/Type your medical question/i);
  const button = screen.getByRole("button", { name: /Send Message/i });

  await userEvent.type(textarea, "Is aspirin safe?");
  expect(button).not.toBeDisabled();
});

test("displays response after successful fetch", async () => {
  fetch
    .mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        conversation_id: 1,
      }),
    })
    .mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        turn_number: 1,
        prompt_type: "direct",
        runs_per_model: 1,
        responses: [
          {
            model_name: "claude",
            run_number: 1,
            response_text: "Aspirin is generally safe when used properly.",
            response_time: 1.2,
            scored: false,
            id: 123,
          },
        ],
      }),
    });

  render(<App />);

  const textarea = screen.getByPlaceholderText(/Type your medical question/i);
  const button = screen.getByRole("button", { name: /Send Message/i });

  await userEvent.type(textarea, "Is aspirin safe?");
  await userEvent.click(button);

  await waitFor(() => {
    expect(screen.getByText(/Aspirin is generally safe/i)).toBeInTheDocument();
  });
});
