import {
    createBrowserRouter,
    createRoutesFromElements,
    Route,
} from "react-router-dom";

import { Layout } from "./pages/Layout";
import { Home } from "./pages/Home";
import { Single } from "./pages/Single";
import { Demo } from "./pages/Demo";
import { Register } from "./pages/Register";
import { Login } from "./pages/Login";
import { Friends } from "./pages/Friends";
import { FriendProfile } from "./pages/FriendProfile";
import Messages from "./pages/Messages";

export const router = createBrowserRouter(
    createRoutesFromElements(
        <Route path="/" element={<Layout />} errorElement={<h1>Not found!</h1>}>
            <Route path="/" element={<Home />} />
            <Route path="/demo" element={<Demo />} />
            <Route path="/single/:theId" element={<Single />} />
            <Route path="/register" element={<Register />} />
            <Route path="/login" element={<Login />} />
            <Route path="/friends" element={<Friends />} />
            <Route path="/friends/:userId" element={<FriendProfile />} />
            <Route path="/messages" element={<Messages />} />
            <Route path="/messages/:conversationId" element={<Messages />} />
        </Route>
    )
);