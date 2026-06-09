import { useState } from "react";
import { Modal, Form, Button, Alert, Spinner } from "react-bootstrap";
import { FiAtSign, FiLock, FiCheckCircle } from "react-icons/fi";

const MODAL_CSS = `
.sq-reset-modal .modal-content {
	background: #161922;
	color: #e9ecef;
	border: 1px solid #262a36;
	border-radius: 14px;
}
.sq-reset-modal .form-control,
.sq-reset-modal .form-control:focus {
	background-color: #0f111a !important;
	color: #e9ecef !important;
	border-color: #2a2f42 !important;
	box-shadow: none;
}
.sq-reset-modal .form-control::placeholder { color: #6c757d; }
.sq-reset-modal .form-label {
	color: #adb5bd;
	font-size: 0.78rem;
	text-transform: uppercase;
	letter-spacing: 0.04em;
	margin-bottom: 0.35rem;
}
.sq-reset-submit {
	background: linear-gradient(135deg, #6366f1, #4f46e5);
	border: none;
	font-weight: 600;
}
.sq-reset-submit:hover,
.sq-reset-submit:focus {
	background: linear-gradient(135deg, #4f46e5, #4338ca);
}
`;

export const ResetPasswordModal = ({ show, onHide }) => {
	const [identifier, setIdentifier] = useState("");
	const [password, setPassword] = useState("");
	const [confirm, setConfirm] = useState("");
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState("");
	const [done, setDone] = useState(false);

	const resetState = () => {
		setIdentifier("");
		setPassword("");
		setConfirm("");
		setError("");
		setDone(false);
		setLoading(false);
	};

	const close = () => {
		resetState();
		onHide();
	};

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
			<style>{MODAL_CSS}</style>
			<Modal show={show} onHide={close} centered dialogClassName="sq-reset-modal">
				<Modal.Header closeButton closeVariant="white" className="border-secondary">
					<Modal.Title>Reset your password</Modal.Title>
				</Modal.Header>
				<Modal.Body>
					{done ? (
						<div className="text-center py-2">
							<FiCheckCircle size={44} color="#22c55e" className="mb-3" />
							<h5 className="mb-2">Password updated</h5>
							<p className="text-secondary mb-3">
								You can now log in with your new password.
							</p>
							<Button className="sq-reset-submit w-100" onClick={close}>
								Close
							</Button>
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
									className="sq-reset-submit w-100 py-2"
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
						</>
					)}
				</Modal.Body>
			</Modal>
		</>
	);
};

export default ResetPasswordModal;
