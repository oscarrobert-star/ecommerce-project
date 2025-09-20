import React, { useEffect, useState } from "react";
import { Container, Table, Button, Spinner } from "react-bootstrap";
import { useNavigate } from "react-router-dom";

const CART_ID_KEY = "cart_id"; // Use localStorage to persist cart_id
const CART_ITEMS_KEY = "cart"; // Define a constant for your cart items key

export default function CartPage() {
    const navigate = useNavigate();
    const [cart, setCart] = useState([]);
    const [loading, setLoading] = useState(true);

    const cartId = localStorage.getItem(CART_ID_KEY);

    const fetchCart = async () => {
        try {
            const response = await fetch(`${import.meta.env.VITE_BASE_URL}/cart`, {
                method: "GET",
                headers: {
                    "x-cart-id": cartId || "",
                },
            });

            if (response.status === 404) {
                setCart([]);
                localStorage.removeItem(CART_ITEMS_KEY); // Clear cart items if 404
                localStorage.removeItem(CART_ID_KEY); // Clear cart_id if 404
                setLoading(false);
                return;
            }

            const data = await response.json();
            if (!cartId && data.cart_id) {
                localStorage.setItem(CART_ID_KEY, data.cart_id);
            }
            setCart(data.items || []);

            localStorage.setItem(CART_ITEMS_KEY, JSON.stringify(data.items || []));

        } catch (err) {
            console.error("Failed to fetch cart:", err);
            localStorage.removeItem(CART_ITEMS_KEY); // Clear cart items on fetch error too
        } finally {
            setLoading(false);
        }
    };

    const removeFromCart = async (productId) => {
        try {
            const response = await fetch(`${import.meta.env.VITE_BASE_URL}/cart/remove`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "x-cart-id": localStorage.getItem(CART_ID_KEY),
                },
                body: JSON.stringify({ product_id: productId }),
            });

            if (response.ok) {
                await fetchCart();
            }
        } catch (err) {
            console.error("Failed to remove item:", err);
        }
    };

    const updateQuantity = async (productId, action) => {
        try {
            const item = cart.find((item) => item.product_id === productId);
            if (!item) return;

            const newQuantity = item.quantity + (action === "increase" ? 1 : -1);

            if (newQuantity <= 0) {
                await removeFromCart(productId);
                return;
            }

            await fetch(`${import.meta.env.VITE_BASE_URL}/cart/edit`, {
                method: "PATCH",
                headers: {
                    "Content-Type": "application/json",
                    "x-cart-id": localStorage.getItem(CART_ID_KEY),
                },
                body: JSON.stringify({
                    product_id: productId,
                    quantity: newQuantity,
                }),
            });

            await fetchCart();
        } catch (err) {
            console.error("Failed to update quantity:", err);
        }
    };

    const calculateTotal = () => {
        return cart.reduce((total, item) => total + parseFloat(item.price) * item.quantity, 0).toFixed(2);
    };

    const handleContinueShopping = () => {
        navigate("/");
    };

    useEffect(() => {
        fetchCart();
    }, []);

    return (
        <Container className="mt-5">
            <h2 className="text-center mb-4">Shopping Cart</h2>

            {loading ? (
                <div className="text-center"><Spinner animation="border" /></div>
            ) : cart.length > 0 ? (
                <>
                    <Table striped bordered hover responsive>
                        <thead>
                            <tr>
                                <th>Product</th>
                                <th>Price</th>
                                <th>Quantity</th>
                                <th>Total</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            {cart.map((item, index) => (
                                <tr key={item.product_id || index}>
                                    <td>
                                        <a
                                            href={`http://client.localhost/product/${item.product_id}`}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                        >
                                            {item.product_name || "Unnamed Product"}
                                        </a>
                                    </td>
                                    <td>${parseFloat(item.price).toFixed(2)}</td>
                                    <td>
                                        <Button
                                            variant="outline-secondary"
                                            onClick={() => updateQuantity(item.product_id, "decrease")}
                                            disabled={item.quantity <= 1}
                                        >
                                            -
                                        </Button>
                                        <span className="mx-3">{item.quantity}</span>
                                        <Button
                                            variant="outline-secondary"
                                            onClick={() => updateQuantity(item.product_id, "increase")}
                                        >
                                            +
                                        </Button>
                                    </td>
                                    <td>${(parseFloat(item.price) * item.quantity).toFixed(2)}</td>
                                    <td>
                                        <Button
                                            variant="danger"
                                            onClick={() => removeFromCart(item.product_id)}
                                        >
                                            Remove
                                        </Button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </Table>
                    <div className="d-flex justify-content-between">
                        <h3>Total: ${calculateTotal()}</h3>
                        <Button variant="primary" onClick={() => navigate("/checkout")}>
                            Proceed to Checkout
                        </Button>
                    </div>
                </>
            ) : (
                <div className="text-center">
                    <p>Your cart is empty!</p>
                </div>
            )}

            <div className="d-flex justify-content-center mt-4">
                <Button variant="outline-secondary" onClick={handleContinueShopping}>
                    Continue Shopping
                </Button>
            </div>
        </Container>
    );
}
