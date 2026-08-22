import React from "react";

export default class ReactErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error, info) {
    console.error("ChatAssist React crash:", error);
    console.error("Component stack:", info.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            minHeight: "100vh",
            background: "#111",
            color: "white",
            padding: "40px",
            fontFamily: "sans-serif",
          }}
        >
          <h2>ChatAssist encountered an error</h2>
          <p>
            The interface could not continue rendering. Check the browser
            console for the exact error.
          </p>

          <pre style={{ whiteSpace: "pre-wrap", color: "#ff8080" }}>
            {this.state.error?.stack || String(this.state.error)}
          </pre>
        </div>
      );
    }

    return this.props.children;
  }
}
