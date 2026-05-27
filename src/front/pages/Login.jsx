import { useState } from "react";
import { useNavigate } from "react-router-dom";

export const Login = () => {
	const navigate = useNavigate();

	const [email, setEmail] = useState("");
	const [password, setPassword] = useState("");

	const handleLogin = async (e) => {
		e.preventDefault();

		try {
			const response = await fetch(`${import.meta.env.VITE_BACKEND_URL}/api/login`, {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
				},
				body: JSON.stringify({
					email,
					password,
				}),
			});

			const data = await response.json();

			if (!response.ok) {
				alert(data.msg || "Login error");
				return;
			}

			localStorage.setItem("token", data.token);
			localStorage.setItem("user", JSON.stringify(data.user));

			alert("Login successful");
			navigate("/");

		} catch (error) {
			console.error("Login error:", error);
			alert("Server error");
		}
	};

	return (
		<div className="container mt-5">
			<h1>Login</h1>

			<form onSubmit={handleLogin} className="mt-4">
				<div className="mb-3">
					<label className="form-label">Email</label>
					<input
						type="email"
						className="form-control"
						value={email}
						onChange={(e) => setEmail(e.target.value)}
						placeholder="Enter email"
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
					/>
				</div>

				<button type="submit" className="btn btn-primary">
					Login
				</button>
			</form>
		</div>
	);
};