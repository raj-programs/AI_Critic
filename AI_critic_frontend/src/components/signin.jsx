import { SignIn as ClerkSignIn } from "@clerk/react"
import "../styles/signin.css"
export default function SignIn() {
    return (
        <>
        <div className="auth-page">
            <ClerkSignIn routing="path" path="/sign-in" />
        </div>
        </>
    )
}