function SignUp () {
    return (
        <>
        <form action="">
            <label htmlFor="name">
                Enter Your Name
            </label>
            <input type="text" 
            placeholder="Full Name" 
            required/>
            <label htmlFor="username">
                Enter Your Username
            </label>
            <input type="text" 
            placeholder="Username"
            required/>
            <label htmlFor="email">
                Enter Your Email
            </label>
            <input type="email" placeholder="Email" required/>
            <label htmlFor="password">
                Enter Password
            </label>
            <input type="password" placeholder="Password" required/>
            <label htmlFor="confirm-password">
                Retype Password
            </label>
            <input type="password" placeholder="Confirm Password" required/>
            <button type="submit" className="submit-btn">
                Sign In
            </button>
        </form>
        </>
    )
}

export default SignUp