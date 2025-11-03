import React, { useState, useRef, useEffect } from "react";
import { Container, Row, Col, Card, Button, Form, Badge } from "react-bootstrap";
import { useNavigate } from "react-router-dom";
import "../assets/css/homepage.css";
import laptopImg from "../assets/images/laptop2.png";
import phoneImg from "../assets/images/phone.jpg";
import headphonesImg from "../assets/images/headphones.jpg";
import heroImage from "../assets/images/hero-image.jpg";

const productsList = [
    { id: 1, name: "Laptop", description: "High-performance laptop.", price: 999.99, image: laptopImg, category: "Laptops" },
    { id: 2, name: "Smartphone", description: "Latest smartphone features.", price: 699.99, image: phoneImg, category: "Phones" },
    { id: 3, name: "Wireless Headphones", description: "Noise-canceling headphones.", price: 149.99, image: headphonesImg, category: "Accessories" },
];

const bestSellers = [
    { id: 4, name: "Tablet", description: "Powerful and lightweight tablet.", price: 499.99, image: laptopImg, category: "Laptops" },
    { id: 5, name: "Smartwatch", description: "Track your fitness & health.", price: 199.99, image: phoneImg, category: "Accessories" },
];

const newArrivals = [
    { id: 6, name: "Gaming Headset", description: "Immersive gaming experience.", price: 129.99, image: headphonesImg, category: "Accessories" },
    { id: 7, name: "4K Smart TV", description: "Ultra HD entertainment.", price: 1199.99, image: laptopImg, category: "Laptops" },
];

function getOrCreateCartId() {
    let cartId = localStorage.getItem("cart_id");
    if (!cartId) {
        cartId = crypto.randomUUID();
        localStorage.setItem("cart_id", cartId);
    }
    return cartId;
}

export default function HomePage() {
    const navigate = useNavigate();
    const [search, setSearch] = useState("");
    const [cart, setCart] = useState([]);
    const featuredRef = useRef(null);

    useEffect(() => {
        getOrCreateCartId(); // Ensure cart_id exists on page load
    }, []);

    const filteredProducts = productsList.filter((product) =>
        product.name.toLowerCase().includes(search.toLowerCase()) ||
        product.description.toLowerCase().includes(search.toLowerCase())
    );

    const addToCart = async (product) => {
        const cartItem = {
            product_id: product.id,
            product_name: product.name,
            quantity: 1,
            price: product.price.toFixed(2),
        };

        const cartId = getOrCreateCartId();

        try {
            const response = await fetch(`${import.meta.env.VITE_BASE_URL}/cart/add`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-Cart-ID": cartId,
                },
                body: JSON.stringify(cartItem),
            });

            if (!response.ok) {
                throw new Error("Failed to add item to cart.");
            }

            const updatedCart = [...cart];
            const index = updatedCart.findIndex(item => item.product_id === cartItem.product_id);
            if (index !== -1) {
                updatedCart[index].quantity += 1;
            } else {
                updatedCart.push(cartItem);
            }
            setCart(updatedCart);
            localStorage.setItem("cart", JSON.stringify(updatedCart));
        } catch (error) {
            console.error("Error adding to cart:", error);
        }
    };

    const viewCart = () => {
        navigate("/cart");
    };

    const scrollToFeatured = () => {
        featuredRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    return (
        <div className="homepage">
            <section className="hero-section d-flex align-items-center" style={{ backgroundImage: `url(${heroImage})` }}>
                <Container className="text-center text-white">
                    <h1>Welcome to Our Store</h1>
                    <p>Discover amazing products at the best prices</p>
                    <Button variant="light" size="lg" onClick={scrollToFeatured}>Shop Now</Button>
                </Container>
            </section>

            <Container className="p-4">
                <Form.Control
                    type="text"
                    placeholder="Search for products..."
                    className="mb-4 mx-auto search-bar"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                />

                <Button variant="outline-dark" onClick={viewCart} className="position-relative">
                    View Cart
                    {cart.length > 0 && (
                        <Badge bg="danger" className="position-absolute top-0 start-100 translate-middle">{cart.length}</Badge>
                    )}
                </Button>

                <h2 ref={featuredRef} className="text-center mb-4">Featured Products</h2>
                <Row className="justify-content-center">
                    {filteredProducts.map((product) => (
                        <Col key={product.id} md={4} className="d-flex">
                            <Card className="mb-3 shadow-sm flex-fill text-center">
                                <Card.Img variant="top" src={product.image} className="product-img" />
                                <Card.Body>
                                    <Card.Title>{product.name}</Card.Title>
                                    <Card.Text>{product.description}</Card.Text>
                                    <h5 className="text-primary">${product.price.toFixed(2)}</h5>
                                    <div className="d-grid gap-2">
                                        <Button variant="success" onClick={() => addToCart(product)}>Add to Cart</Button>
                                        <Button variant="outline-primary" onClick={() => navigate(`/product/${product.id}`)}>View Details</Button>
                                    </div>
                                </Card.Body>
                            </Card>
                        </Col>
                    ))}
                </Row>

                <h2 className="text-center mt-4">Best Sellers</h2>
                <Row className="justify-content-center">
                    {bestSellers.map((product) => (
                        <Col key={product.id} md={4} className="d-flex">
                            <Card className="mb-3 shadow-sm flex-fill text-center">
                                <Card.Img variant="top" src={product.image} className="product-img" />
                                <Card.Body>
                                    <Card.Title>{product.name}</Card.Title>
                                    <Card.Text>{product.description}</Card.Text>
                                    <h5 className="text-primary">${product.price.toFixed(2)}</h5>
                                    <div className="d-grid gap-2">
                                        <Button variant="success" onClick={() => addToCart(product)}>Add to Cart</Button>
                                        <Button variant="outline-primary" onClick={() => navigate(`/product/${product.id}`)}>View Details</Button>
                                    </div>
                                </Card.Body>
                            </Card>
                        </Col>
                    ))}
                </Row>

                <h2 className="text-center mt-4">New Arrivals</h2>
                <Row className="justify-content-center">
                    {newArrivals.map((product) => (
                        <Col key={product.id} md={4} className="d-flex">
                            <Card className="mb-3 shadow-sm flex-fill text-center">
                                <Card.Img variant="top" src={product.image} className="product-img" />
                                <Card.Body>
                                    <Card.Title>{product.name}</Card.Title>
                                    <Card.Text>{product.description}</Card.Text>
                                    <h5 className="text-primary">${product.price.toFixed(2)}</h5>
                                    <div className="d-grid gap-2">
                                        <Button variant="success" onClick={() => addToCart(product)}>Add to Cart</Button>
                                        <Button variant="outline-primary" onClick={() => navigate(`/product/${product.id}`)}>View Details</Button>
                                    </div>
                                </Card.Body>
                            </Card>
                        </Col>
                    ))}
                </Row>
            </Container>
        </div>
    );
}
