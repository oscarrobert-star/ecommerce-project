import React, { useState, useRef } from "react";
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

export default function HomePage() {
    const navigate = useNavigate();
    const [search, setSearch] = useState("");
    const [cart, setCart] = useState([]);
    const featuredRef = useRef(null);

    const filteredProducts = productsList.filter((product) => {
        return product.name.toLowerCase().includes(search.toLowerCase()) || 
               product.description.toLowerCase().includes(search.toLowerCase());
    });

    // const addToCart = (product) => {
    //     setCart((prevCart) => [...prevCart, product]);
    // };
    const addToCart = (product) => {
        let updatedCart = [...cart];
        const existingProductIndex = updatedCart.findIndex(item => item.id === product.id);
    
        if (existingProductIndex !== -1) {
            // If product already exists in cart, increase quantity
            updatedCart[existingProductIndex].quantity += 1;
        } else {
            // If product doesn't exist, add it with quantity 1
            updatedCart.push({ ...product, quantity: 1 });
        }
    
        setCart(updatedCart);
        localStorage.setItem("cart", JSON.stringify(updatedCart));  // Save updated cart to localStorage
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

                {/* Cart Icon with Badge */}
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
