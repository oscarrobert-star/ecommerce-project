import React, { useState } from "react";
import { Container, Row, Col, Table, Button } from "react-bootstrap";
import { useNavigate } from "react-router-dom";

export default function CartPage() {
    const navigate = useNavigate();
    const [cart, setCart] = useState(() => {
        const savedCart = JSON.parse(localStorage.getItem("cart"));
        return savedCart || [];
    });

    // Update cart in localStorage
    const updateCartInLocalStorage = (updatedCart) => {
        localStorage.setItem("cart", JSON.stringify(updatedCart));
    };

    const removeFromCart = (productId) => {
        const updatedCart = cart.filter((item) => item.id !== productId);
        setCart(updatedCart);
        updateCartInLocalStorage(updatedCart);
    };

    const updateQuantity = (productId, action) => {
        const updatedCart = cart.map((item) =>
            item.id === productId
                ? {
                      ...item,
                      quantity: action === "increase" ? item.quantity + 1 : item.quantity - 1,
                  }
                : item
        );
        setCart(updatedCart);
        updateCartInLocalStorage(updatedCart);
    };

    const calculateTotal = () => {
        return cart.reduce((total, item) => total + item.price * item.quantity, 0).toFixed(2);
    };

    const handleContinueShopping = () => {
        navigate("/"); // Navigate back to homepage or products page
    };

    return (
        <Container className="mt-5">
            <h2 className="text-center mb-4">Shopping Cart</h2>

            {cart.length > 0 ? (
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
                            {cart.map((item) => (
                                <tr key={item.id}>
                                    <td>
                                        <a href={`/product/${item.id}`}>{item.name}</a>
                                    </td>
                                    <td>${item.price.toFixed(2)}</td>
                                    <td>
                                        <Button
                                            variant="outline-secondary"
                                            onClick={() => updateQuantity(item.id, "decrease")}
                                            disabled={item.quantity <= 1}
                                        >
                                            -
                                        </Button>
                                        <span className="mx-3">{item.quantity}</span>
                                        <Button
                                            variant="outline-secondary"
                                            onClick={() => updateQuantity(item.id, "increase")}
                                        >
                                            +
                                        </Button>
                                    </td>
                                    <td>${(item.price * item.quantity).toFixed(2)}</td>
                                    <td>
                                        <Button
                                            variant="danger"
                                            onClick={() => removeFromCart(item.id)}
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
                        <Button
                            variant="primary"
                            onClick={() => navigate("/checkout")}
                        >
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
