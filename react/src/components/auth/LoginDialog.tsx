import React, { useState, useEffect, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { Button } from '../ui/button'
import { Input } from '../ui/input'
import { Label } from '../ui/label'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../ui/dialog'
import { startDeviceAuth, pollDeviceAuth, saveAuthData, auth_login, auth_register } from '../../api/auth'
import { updateJaazApiKey } from '../../api/config'
import { useAuth } from '../../contexts/AuthContext'
import { useConfigs, useRefreshModels } from '../../contexts/configs'

export function LoginDialog() {
  const [authMessage, setAuthMessage] = useState('')
  const [activeTab, setActiveTab] = useState<'login' | 'register'>('login')
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isFormLoading, setIsFormLoading] = useState(false)

  const { refreshAuth, authStatus, isLoading } = useAuth()
  const { showLoginDialog: open, setShowLoginDialog } = useConfigs()
  const refreshModels = useRefreshModels()
  const { t } = useTranslation()
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null)

  const shouldRender = !isLoading && !authStatus.is_logged_in

  useEffect(() => {
    if (!shouldRender) return
    setAuthMessage('')
    setUsername('')
    setEmail('')
    setPassword('')
    setIsFormLoading(false)

    if (!open) {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current)
        pollingIntervalRef.current = null
      }
    }
  }, [open, shouldRender])

  useEffect(() => {
    if (!shouldRender) return
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current)
      }
    }
  }, [shouldRender])

  const handleSuccess = async (token: string, user_info: any) => {
    saveAuthData(token, user_info)
    await updateJaazApiKey(token)

    setAuthMessage(t('common:auth.loginSuccessMessage', 'Login successful!'))

    try {
      await refreshAuth()
      refreshModels()
    } catch (error) {
      console.error('Failed to refresh auth status:', error)
    }

    setTimeout(() => setShowLoginDialog(false), 1500)
  }

  const handleLocalLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsFormLoading(true)
    setAuthMessage('')

    try {
      const result = await auth_login(username, password)
      await handleSuccess(result.token, result.user_info)
    } catch (error: any) {
      console.error('Login failed:', error)
      setAuthMessage(error.message || 'Login failed')
    } finally {
      setIsFormLoading(false)
    }
  }

  const handleLocalRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsFormLoading(true)
    setAuthMessage('')

    try {
      const result = await auth_register(username, email, password)
      await handleSuccess(result.token, result.user_info)
    } catch (error: any) {
      console.error('Registration failed:', error)
      setAuthMessage(error.message || 'Registration failed')
    } finally {
      setIsFormLoading(false)
    }
  }

  const startPolling = (code: string) => {
    console.log('Starting polling for device code:', code)

    const poll = async () => {
      try {
        const result = await pollDeviceAuth(code)
        console.log('Poll result:', result)

        if (result.status === 'authorized') {
          if (result.token && result.user_info) {
            await handleSuccess(result.token, result.user_info)
          }
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current)
            pollingIntervalRef.current = null
          }
        } else if (result.status === 'expired') {
          setAuthMessage(t('common:auth.authExpiredMessage'))
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current)
            pollingIntervalRef.current = null
          }
        } else if (result.status === 'error') {
          setAuthMessage(result.message || t('common:auth.authErrorMessage'))
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current)
            pollingIntervalRef.current = null
          }
        } else {
          setAuthMessage(t('common:auth.waitingForBrowser'))
        }
      } catch (error) {
        console.error('Polling error:', error)
        setAuthMessage(t('common:auth.pollErrorMessage'))
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current)
          pollingIntervalRef.current = null
        }
      }
    }

    poll()
    pollingIntervalRef.current = setInterval(poll, 1000)
  }

  const handleDeviceLogin = async () => {
    try {
      setAuthMessage(t('common:auth.preparingLoginMessage'))

      const result = await startDeviceAuth()
      setAuthMessage(result.message)

      startPolling(result.code)
    } catch (error) {
      console.error('登录请求失败:', error)
      setAuthMessage(t('common:auth.loginRequestFailed'))
    }
  }

  return shouldRender ? (
    <Dialog open={open} onOpenChange={setShowLoginDialog}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>{t('common:auth.loginToJaaz', 'Login to Jaaz')}</DialogTitle>
        </DialogHeader>

        <div className="flex border-b mb-4">
          <button
            className={`flex-1 py-2 text-sm font-medium ${activeTab === 'login' ? 'border-b-2 border-primary text-primary' : 'text-muted-foreground'}`}
            onClick={() => { setActiveTab('login'); setAuthMessage(''); }}
          >
            Login
          </button>
          <button
            className={`flex-1 py-2 text-sm font-medium ${activeTab === 'register' ? 'border-b-2 border-primary text-primary' : 'text-muted-foreground'}`}
            onClick={() => { setActiveTab('register'); setAuthMessage(''); }}
          >
            Register
          </button>
        </div>

        <div className="space-y-4">
          {activeTab === 'login' ? (
            <form onSubmit={handleLocalLogin} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="username">Username</Label>
                <Input
                  id="username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  disabled={isFormLoading || !!pollingIntervalRef.current}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  disabled={isFormLoading || !!pollingIntervalRef.current}
                />
              </div>
              <Button type="submit" className="w-full" disabled={isFormLoading || !!pollingIntervalRef.current}>
                {isFormLoading ? 'Logging in...' : 'Login'}
              </Button>
            </form>
          ) : (
            <form onSubmit={handleLocalRegister} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="reg-username">Username</Label>
                <Input
                  id="reg-username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  disabled={isFormLoading || !!pollingIntervalRef.current}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="reg-email">Email</Label>
                <Input
                  id="reg-email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  disabled={isFormLoading || !!pollingIntervalRef.current}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="reg-password">Password</Label>
                <Input
                  id="reg-password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  disabled={isFormLoading || !!pollingIntervalRef.current}
                />
              </div>
              <Button type="submit" className="w-full" disabled={isFormLoading || !!pollingIntervalRef.current}>
                {isFormLoading ? 'Registering...' : 'Register'}
              </Button>
            </form>
          )}

          {authMessage && (
            <div className="text-sm text-center text-muted-foreground mt-2 p-2 bg-muted rounded-md">
              {authMessage}
            </div>
          )}

          <div className="relative my-4">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-background px-2 text-muted-foreground">
                Or continue with
              </span>
            </div>
          </div>

          <Button
            type="button"
            variant="outline"
            onClick={handleDeviceLogin}
            disabled={isFormLoading || !!pollingIntervalRef.current}
            className="w-full"
          >
            {t('common:auth.startLogin', 'Device Login (Browser)')}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  ) : null
}
