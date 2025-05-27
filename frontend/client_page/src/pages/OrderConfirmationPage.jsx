import React, { useEffect, useState, useCallback } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Container, Alert, Spinner, Button, Card, ListGroup, Row, Col } from "react-bootstrap";

// Constants for localStorage keys
const CART_ID_KEY = "cart_id";
const CART_ITEMS_KEY = "cart";
const LAST_ORDER_REFERENCE_KEY = "last_order_reference";

export default function OrderConfirmationPage() {
    const location = useLocation();
    const navigate = useNavigate();

    const [loading, setLoading] = useState(true);
    const [message, setMessage] = useState("");
    const [status, setStatus] = useState("loading"); // success | pending | failed | loading
    const [order, setOrder] = useState(null);

    const useQuery = () => {
        return new URLSearchParams(location.search);
    };
    const query = useQuery();

    // Debugging: Keep track of renders
    console.log("OrderConfirmationPage: Component rendered.");

    const fetchOrderDetails = useCallback(async (reference) => {
        console.log("fetchOrderDetails: Function invoked for reference:", reference);
        try {
            setMessage("Fetching your order details...");
            const response = await fetch(`${import.meta.env.VITE_BASE_URL}/orders/status/${reference}/`, {
                method: "GET",
                headers: {
                    "Content-Type": "application/json",
                },
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ message: response.statusText }));
                throw new Error(errorData.message || "Failed to fetch order. Please try again.");
            }

            const data = await response.json();
            setOrder(data);

            if (["paid", "completed"].includes(data.payment_status)) {
                setStatus("success");
                setMessage("Your order was successful! Thank you.");
                localStorage.removeItem(CART_ID_KEY);
                localStorage.removeItem(CART_ITEMS_KEY);
                localStorage.removeItem(LAST_ORDER_REFERENCE_KEY);
            } else if (data.payment_status === "pending") {
                setStatus("pending");
                setMessage("Your payment is pending confirmation. You may check your order history later.");
            } else {
                setStatus("failed");
                setMessage(data.message || "Payment failed or was not completed. Please try again or contact support.");
            }
        } catch (err) {
            console.error("Order fetch error:", err);
            setStatus("failed");
            setMessage(err.message || "Something went wrong. Please contact support.");
        } finally {
            setLoading(false);
            console.log("fetchOrderDetails: Finished setting loading to false.");
        }
    }, []); // Empty dependency array: this function is created once on mount and never changes.

    useEffect(() => {
        console.log("useEffect: Effect function started.");
        const queryParams = new URLSearchParams(location.search);
        const reference = queryParams.get("reference");

        if (!reference) {
            setMessage("Missing order reference.");
            setStatus("failed");
            setLoading(false);
            console.log("useEffect: No reference found, setting status to failed.");
            return;
        }

        console.log("useEffect: Calling fetchOrderDetails with reference:", reference);
        fetchOrderDetails(reference);

        // No cleanup for setTimeout needed as there's no setTimeout.
        // No cleanup for any subscriptions needed either, as it's a one-off fetch.
    }, [location.search, fetchOrderDetails]); // Dependencies

    const handleContinueShopping = () => {
        navigate("/");
    };

    return (
        <Container className="mt-5">
            {loading ? (
                <div className="text-center">
                    <Spinner animation="border" role="status" />
                    <p className="mt-3">{message || "Loading..."}</p>
                </div>
            ) : (
                <>
                    {status === "success" && (
                        <Alert variant="success" className="text-center">
                            <h4>Order Confirmed!</h4>
                            <p>{message}</p>
                        </Alert>
                    )}

                    {status === "pending" && (
                        <Alert variant="warning" className="text-center">
                            <h4>Order Pending</h4>
                            <p>{message}</p>
                        </Alert>
                    )}

                    {status === "failed" && (
                        <Alert variant="danger" className="text-center">
                            <h4>Order Failed</h4>
                            <p>{message}</p>
                            <Button variant="danger" onClick={() => navigate("/cart")}>
                                Return to Cart
                            </Button>
                        </Alert>
                    )}

                    {order && status !== "failed" && (
                        <Card className="mt-4">
                            <Card.Header as="h5">Order Details</Card.Header>
                            <Card.Body>
                                <Row className="mb-2">
                                    <Col md={6}><strong>Order ID:</strong> {order.id}</Col>
                                    <Col md={6}><strong>Reference:</strong> {order.payment_reference}</Col>
                                </Row>
                                <Row className="mb-2">
                                    <Col md={6}>
                                        <strong>Status:</strong>{" "}
                                        <span className={`badge ${
                                            order.payment_status === "paid" || order.payment_status === "completed"
                                                ? "bg-success"
                                                : order.payment_status === "pending"
                                                ? "bg-warning text-dark"
                                                : "bg-danger"
                                        }`}>
                                            {order.payment_status ? order.payment_status.toUpperCase() : "UNKNOWN"}
                                        </span>
                                    </Col>
                                    <Col md={6}>
                                        <strong>Total:</strong> $
                                        {order.total_amount ? Number(order.total_amount).toFixed(2) : "0.00"}
                                    </Col>
                                </Row>
                                <Row className="mb-2">
                                    <Col><strong>Created:</strong> {new Date(order.created_at).toLocaleString()}</Col>
                                </Row>

                                <h6 className="mt-4">Items:</h6>
                                <ListGroup>
                                    {(order.items || []).map((item, i) => (
                                        <ListGroup.Item key={item.id || i}>
                                            <Row>
                                                <Col>{item.product_name}</Col>
                                                <Col className="text-end">
                                                    {item.quantity} x ${Number(item.price).toFixed(2)} = $
                                                    {(Number(item.quantity) * Number(item.price)).toFixed(2)}
                                                </Col>
                                            </Row>
                                        </ListGroup.Item>
                                    ))}
                                </ListGroup>
                            </Card.Body>
                        </Card>
                    )}

                    <div className="text-center mt-4">
                        <Button variant="primary" onClick={handleContinueShopping}>
                            Continue Shopping
                        </Button>
                    </div>
                </>
            )}
        </Container>
    );
}