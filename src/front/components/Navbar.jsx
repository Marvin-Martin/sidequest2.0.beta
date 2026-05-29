import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";

import useGlobalReducer from "../hooks/useGlobalReducer";
import { api } from "../services/api";

import Container from "react-bootstrap/Container";
import NavbarBs from "react-bootstrap/Navbar";
import Nav from "react-bootstrap/Nav";
import Badge from "react-bootstrap/Badge";
import Button from "react-bootstrap/Button";

import { NotificationBell } from "./NotificationBell.jsx";
import { FiMenu, FiMail, FiUsers } from "react-icons/fi";

const POLL_INTERVAL = 8000;

export const Navbar = () => {
    const navigate = useNavigate();
    const { store, dispatch } = useGlobalReducer();

    const fetchConversations = async () => {
        if (!localStorage.getItem("token")) return;
        try {
            const data = await api.get("/conversations");
            dispatch({ type: "set_chat_rooms", payload: data });
        } catch (_) { /* silencioso */ }
    };

    useEffect(() => {
        fetchConversations();
        const id = setInterval(fetchConversations, POLL_INTERVAL);
        return () => clearInterval(id);
    }, [store.token]);

    const handleLogout = () => {
        dispatch({ type: "logout" });
        navigate("/login");
    };

    const totalUnread = (store.chatRooms || []).reduce(
        (sum, r) => sum + (r.unread_count || 0), 0
    );

    const userLabel = store.user?.username || store.user?.email || "";

    return (
        <NavbarBs bg="dark" variant="dark" className="px-4 py-3 fixed-top">
            <Container fluid className="d-flex justify-content-between">
                <Link to="/" className="text-decoration-none">
                    <NavbarBs.Brand className="fw-bold fs-3">SQ</NavbarBs.Brand>
                </Link>

                <Nav className="d-flex flex-row align-items-center gap-4">
                    {store.token ? (
                        <>
                            <span className="text-light d-none d-md-block fw-bold">
                                Hola {userLabel}
                            </span>

                            <Link to="/friends" className="text-decoration-none" title="Friends">
                                <Button variant="dark" className="border-0 d-flex align-items-center gap-1">
                                    <FiUsers size={24} color="white" />
                                    <span className="text-light d-none d-md-inline small">Friends</span>
                                </Button>
                            </Link>

                            <NotificationBell />

                            <Link to="/messages" className="text-decoration-none">
                                <Button variant="dark" className="position-relative border-0">
                                    <FiMail size={28} color="white" />
                                    {totalUnread > 0 && (
                                        <Badge bg="danger" pill
                                            className="position-absolute top-0 start-100 translate-middle">
                                            {totalUnread > 99 ? "99+" : totalUnread}
                                        </Badge>
                                    )}
                                </Button>
                            </Link>

                            <Button variant="outline-danger" size="sm" onClick={handleLogout}>
                                Salir
                            </Button>
                        </>
                    ) : (
                        <>
                            <Link to="/login">
                                <Button variant="primary" size="sm" className="me-2">Ingresar</Button>
                            </Link>
                            <Link to="/register">
                                <Button variant="success" size="sm">Registro</Button>
                            </Link>
                        </>
                    )}

                    <FiMenu size={34} color="white" style={{ cursor: "pointer" }} />
                </Nav>
            </Container>
        </NavbarBs>
    );
};