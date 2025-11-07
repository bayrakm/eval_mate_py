import NextAuth from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";

const handler = NextAuth({
  providers: [
    CredentialsProvider({
      name: "Credentials",
      credentials: {
        email: {
          label: "Email",
          type: "email",
          placeholder: "demo@example.com",
        },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          return null;
        }

        const demoEmail = process.env.NEXTAUTH_DEMO_EMAIL || "demo@example.com";
        const demoPassword = process.env.NEXTAUTH_DEMO_PASSWORD || "demo123";

        if (
          credentials.email.toLowerCase() === demoEmail.toLowerCase() &&
          credentials.password === demoPassword
        ) {
          return {
            id: "demo-user",
            name: "Demo User",
            email: demoEmail,
            role: "demo",
          };
        }

        return null;
      },
    }),
  ],
  session: {
    strategy: "jwt",
  },
  pages: {
    signIn: "/login",
  },
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.user = user;
      }
      return token;
    },
    async session({ session, token }) {
      if (token?.user) {
        session.user = token.user;
      }
      return session;
    },
  },
});

export { handler as GET, handler as POST };
