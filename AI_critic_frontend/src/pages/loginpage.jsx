function Login() {
    return (
        <>
        <form action="">
            <label htmlFor="username_email">
                Enter Your Username or Email
            </label>
            <input type="text" 
            placeholder="Email or Username" 
            required/>

            <label htmlFor="password">
                Enter Your Password
            </label>
            <input type="password" placeholder="password" required/>

            <button className="btn">
                Login
            </button>
        </form>
        </>
    )
}

export default Login