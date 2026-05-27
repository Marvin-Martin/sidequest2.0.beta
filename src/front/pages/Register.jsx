import { useState } from "react";
import { useNavigate } from "react-router-dom";

export const Register = () => {
	const navigate = useNavigate();

	const [email, setEmail] = useState("");
	const [password, setPassword] = useState("");

	const handleRegister = async (e) => {
		e.preventDefault();

		try {
			const response = await fetch(`${import.meta.env.VITE_BACKEND_URL}/api/register`, {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
				},
				body: JSON.stringify({
					email: email,
					password: password,
				}),
			});

			const data = await response.json();

			if (!response.ok) {
				alert(data.msg || "Error creating user");
				return;
			}

			alert("User registered successfully");
			navigate("/login");

		} catch (error) {
			console.error("Register error:", error);
			alert("Server error");
		}
	};

	return (
		<div className="container mt-5">
			<h1>Register</h1>

			<form onSubmit={handleRegister} className="mt-4">
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
					Register
				</button>
			</form>
		</div>
	);
};