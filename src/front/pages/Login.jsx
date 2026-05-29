import { useState } from "react";
import { useNavigate } from "react-router-dom";
import useGlobalReducer from "../hooks/useGlobalReducer";
import { api } from "../services/api";

export const Login = () => {
    const navigate = useNavigate();
    const { dispatch } = useGlobalReducer();

    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const handleLogin = async (e) => {
        e.preventDefault();
        setError("");
        setLoading(true);
        try {
            const data = await api.post("/login", { email, password });
            dispatch({ type: "set_user", payload: data.user });
            dispatch({ type: "set_token", payload: data.token });
            navigate("/");
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="container mt-5" style={{ maxWidth: 480, paddingTop: "80px" }}>
            <h1>Login</h1>
            {error && <div className="alert alert-danger mt-3">{error}</div>}
            <form onSubmit={handleLogin} className="mt-4">
                <div className="mb-3">
                    <label className="form-label">Email</label>
                    <input
                        type="email"
                        className="form-control"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="Enter email"
                        required
                    />
                </div>
                <div className="mb-3">
                    <label className="form-label">Password</label>
                    <input
                        type="password"
                        className="form-control"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="Enter password"
                        required
                    />
                </div>
                <button type="submit" className="btn btn-primary" disabled={loading}>
                    {loading ? "Ingresando..." : "Login"}
                </button>
            </form>
        </div>
    );
};