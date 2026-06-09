import { useState } from "react";
import { Link } from "react-router-dom";
import {
	Container,
	Card,
	Form,
	Button,
	Alert,
	Spinner,
} from "react-bootstrap";
import { FiAtSign, FiLock, FiCheckCircle, FiLogIn } from "react-icons/fi";
import logoSideQuest from "../assets/img/logoSideQuest.png";

const AUTH_CSS = `
.sq-auth-wrap {
	min-height: 100vh;
	display: flex;
	align-items: center;
	justify-content: center;
	background: radial-gradient(circle at top, #1a1d29 0%, #0b0d13 70%);
	padding: 4rem 1rem 2rem;
}
.sq-auth-card {
	background: #161922;
	color: #e9ecef;
	border: 1px solid #262a36;
	border-radius: 14px;
	max-width: 420px;
	width: 100%;
	box-shadow: 0 10px 40px rgba(0,0,0,0.4);
}
.sq-auth-card .form-control,
.sq-auth-card .form-control:focus {
	background-color: #0f111a !important;
	color: #e9ecef !important;
	border-color: #2a2f42 !important;
	box-shadow: none;
}
.sq-auth-card .form-control::placeholder { color: #6c757d; }
.sq-auth-card .form-label {
	color: #adb5bd;
	font-size: 0.78rem;
	text-transform: uppercase;
	letter-spacing: 0.04em;
	margin-bottom: 0.35rem;
}
.sq-auth-title {
	font-weight: 700;
	background: linear-gradient(135deg, #6366f1, #ec4899);
	-webkit-background-clip: text;
	-webkit-text-fill-color: transparent;
	background-clip: text;
}
.sq-auth-submit {
	background: linear-gradient(135deg, #6366f1, #4f46e5);
	border: none;
	font-weight: 600;
}
.sq-auth-submit:hover,
.sq-auth-submit:focus {
	background: linear-gradient(135deg, #4f46e5, #4338ca);
}
.sq-auth-link {
	color: #6366f1;
	text-decoration: none;
	font-weight: 600;
}
.sq-auth-link:hover { color: #ec4899; }
.sq-auth-hint {
	color: #6c757d;
	font-size: 0.72rem;
	margin-top: 0.25rem;
}
`;

export const ResetPassword = () => {
	const [identifier, setIdentifier] = useState("");
	const [password, setPassword] = useState("");
	const [confirm, setConfirm] = useState("");
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState("");
	const [done, setDone] = useState(false);

	const handleSubmit = async (e) => {
		e.preventDefault();
		setError("");

		if (password.length < 6) {
			setError("Password must be at least 6 characters.");
			return;
		}
		if (password !== confirm) {
			setError("Passwords don't match.");
			return;
		}

		setLoading(true);
		try {
			const res = await fetch(
				`${import.meta.env.VITE_BACKEND_URL}/api/reset-password`,
				{
					method: "POST",
					headers: { "Content-Type": "application/json" },
					body: JSON.stringify({ identifier, password }),
				}
			);
			const data = await res.json().catch(() => ({}));
			if (!res.ok) {
				setError(data.msg || "Could not reset your password.");
				return;
			}
			setDone(true);
		} catch (err) {
			console.error("Reset password error:", err);
			setError("Server error. Please try again later.");
		} finally {
			setLoading(false);
		}
	};

	return (
		<>
			<style>{AUTH_CSS}</style>

			<div className="sq-auth-wrap">
				<Container className="d-flex justify-content-center">
					<Card className="sq-auth-card p-4">
						<h2 className="sq-auth-title text-center mb-1">
							<img
								src={logoSideQuest}
								alt="SideQuest"
								style={{ filter: "brightness(0) invert(1)", height: "54px", width: "auto" }}
							/>
						</h2>
						<p className="text-center text-secondary mb-4">Reset your password</p>

						{done ? (
							<div className="text-center">
								<FiCheckCircle size={48} color="#22c55e" className="mb-3" />
								<h4 className="text-light mb-2">Password updated</h4>
								<p className="text-secondary">
									You can now log in with your new password.
								</p>
								<Link to="/login" className="sq-auth-submit btn w-100 py-2 mt-2 text-white">
									<FiLogIn className="me-2" /> Go to login
								</Link>
							</div>
						) : (
							<>
								{error && (
									<Alert variant="danger" onClose={() => setError("")} dismissible>
										{error}
									</Alert>
								)}

								<Form onSubmit={handleSubmit}>
									<Form.Group className="mb-3">
										<Form.Label>
											<FiAtSign className="me-2" /> Email or username
										</Form.Label>
										<Form.Control
											type="text"
											value={identifier}
											onChange={(e) => setIdentifier(e.target.value)}
											placeholder="alex@example.com or alexchen"
											required
											autoComplete="username"
										/>
									</Form.Group>

									<Form.Group className="mb-3">
										<Form.Label>
											<FiLock className="me-2" /> New password
										</Form.Label>
										<Form.Control
											type="password"
											value={password}
											onChange={(e) => setPassword(e.target.value)}
											placeholder="Enter new password"
											required
											minLength={6}
											autoComplete="new-password"
										/>
									</Form.Group>

									<Form.Group className="mb-4">
										<Form.Label>
											<FiLock className="me-2" /> Confirm password
										</Form.Label>
										<Form.Control
											type="password"
											value={confirm}
											onChange={(e) => setConfirm(e.target.value)}
											placeholder="Re-enter new password"
											required
											minLength={6}
											autoComplete="new-password"
										/>
									</Form.Group>

									<Button
										type="submit"
										className="sq-auth-submit w-100 py-2"
										disabled={loading}
									>
										{loading ? (
											<>
												<Spinner size="sm" animation="border" /> Updating...
											</>
										) : (
											"Update password"
										)}
									</Button>
								</Form>

								<div className="text-center mt-4 text-secondary small">
									<Link to="/login" className="sq-auth-link">
										Back to login
									</Link>
								</div>
							</>
						)}
					</Card>
				</Container>
			</div>
		</>
	);
};

export default ResetPassword;
