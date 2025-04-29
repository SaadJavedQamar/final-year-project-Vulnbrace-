<?php
session_start();
error_reporting(0);
include('includes/config.php');

if (isset($_POST['submit'])) {
    // Registration Logic (unchanged)
    $name = $_POST['fullname'];
    $email = $_POST['emailid'];
    $contactno = $_POST['contactno'];
    $password = $_POST['password'];

    $query = mysqli_query($con, "INSERT INTO users(name, email, contactno, password) VALUES('$name', '$email', '$contactno', '$password')");
    if ($query) {
        header("Location: login.php");
        exit();
    } else {
        echo "<script>alert('Not registered, something went wrong');</script>";
    }
}

if (isset($_POST['login'])) {
    // Login Logic
    $name = $_POST['name'];
    $password = $_POST['password'];

    // Check for XSS using raw user input
    if (strpos($name, '<') !== false || strpos($password, '<') !== false) {
        $api_url = 'http://localhost:5000/classify';
        $payload = json_encode([
            'type' => 'xss',
            'user_input' => $name . ' ' . $password
        ]);

        $ch = curl_init($api_url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, $payload);
        curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
        $response = curl_exec($ch);
        $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        if ($http_code === 200 && $response) {
            $result = json_decode($response, true);
            if ($result['prediction'] === 'malicious') {
                $_SESSION['errmsg'] = "Suspicious activity detected. Please try again.";
                header("Location: login.php");
                exit();
            }
        }
    }

    // Check for SQLi using the full SQL query (original working logic)
    $query_string = "SELECT * FROM users WHERE name='$name' AND password='$password'";
    $api_url = 'http://localhost:5000/classify';
    $payload = json_encode([
        'type' => 'sqli',
        'query' => $query_string
    ]);

    $ch = curl_init($api_url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, $payload);
    curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
    $response = curl_exec($ch);
    $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    if ($http_code !== 200 || !$response) {
        $_SESSION['errmsg'] = "Error communicating with the classification API.";
        header("Location: login.php");
        exit();
    }

    $result = json_decode($response, true);

    if ($result['classification'] === 'Malicious Query') {
        $_SESSION['errmsg'] = "Suspicious activity detected. Please try again.";
        header("Location: login.php");
        exit();
    }

    // Proceed with login if safe
    $query = mysqli_query($con, $query_string);
    $num = mysqli_fetch_array($query);

    if ($num > 0) {
        $_SESSION['login'] = $name;
        $_SESSION['id'] = $num['id'];
        $_SESSION['username'] = $num['name'];
        header("Location: index.php");
        exit();
    } else {
        $_SESSION['errmsg'] = "Invalid username or password.";
        header("Location: login.php");
        exit();
    }
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>Shopping Portal | Sign-in | Signup</title>
    <link rel="stylesheet" href="assets/css/bootstrap.min.css">
    <link rel="stylesheet" href="assets/css/main.css">
    <link rel="stylesheet" href="assets/css/red.css">
</head>
<body>
    <header class="header-style-1">
        <?php include('includes/top-header.php'); ?>
        <?php include('includes/main-header.php'); ?>
        <?php include('includes/menu-bar.php'); ?>
    </header>

    <div class="breadcrumb">
        <div class="container">
            <div class="breadcrumb-inner">
                <ul class="list-inline list-unstyled">
                    <li><a href="home.html">Home</a></li>
                    <li class='active'>Authentication</li>
                </ul>
            </div>
        </div>
    </div>

    <div class="body-content outer-top-bd">
        <div class="container">
            <div class="sign-in-page inner-bottom-sm">
                <div class="row">
                    <div class="col-md-6 col-sm-6 sign-in">
                        <h4 class="">Sign in</h4>
                        <p class="">Hello, Welcome to your account.</p>
                        <form method="POST" action="login.php">
                            <span style="color:red;">
                                <?php echo htmlentities($_SESSION['errmsg']); unset($_SESSION['errmsg']); ?>
                            </span>
                            <div class="form-group">
                                <label for="name">Username:</label>
                                <input type="text" name="name" class="form-control" required>
                            </div>
                            <div class="form-group">
                                <label for="password">Password:</label>
                                <input type="password" name="password" class="form-control" required>
                            </div>
                            <button type="submit" class="btn btn-primary" name="login">Login</button>
                        </form>
                    </div>
                    <div class="col-md-6 col-sm-6 create-new-account">
                        <h4>Create a new account</h4>
                        <form method="POST" action="login.php">
                            <div class="form-group">
                                <label for="fullname">Full Name:</label>
                                <input type="text" name="fullname" class="form-control" required>
                            </div>
                            <div class="form-group">
                                <label for="emailid">Email Address:</label>
                                <input type="email" name="emailid" class="form-control" required>
                            </div>
                            <div class="form-group">
                                <label for="contactno">Contact No:</label>
                                <input type="text" name="contactno" class="form-control" maxlength="10" required>
                            </div>
                            <div class="form-group">
                                <label for="password">Password:</label>
                                <input type="password" name="password" class="form-control" required>
                            </div>
                            <button type="submit" name="submit" class="btn btn-primary">Sign Up</button>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="assets/js/bootstrap.min.js"></script>
</body>
</html>
