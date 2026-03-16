// 对应 commonLayout 的文件: web/app/(commonLayout)/layout.tsx
// 区别: 去除了 Header、HeaderWrapper、RoleRouteGuard、InSiteMessageNotification、PartnerStack、ReadmePanel、GotoAnything、Splash、Zendesk
import type { ReactNode } from 'react'
import * as React from 'react'
import { AppInitializer } from '@/app/components/app-initializer'
import AmplitudeProvider from '@/app/components/base/amplitude'
import GA, { GaType } from '@/app/components/base/ga'
import { AppContextProvider } from '@/context/app-context-provider'
import { EventEmitterContextProvider } from '@/context/event-emitter-provider'
import { ModalContextProvider } from '@/context/modal-context-provider'
import { ProviderContextProvider } from '@/context/provider-context-provider'

const Layout = ({ children }: { children: ReactNode }) => {
  return (
    <>
      <GA gaType={GaType.admin} />
      <AmplitudeProvider />
      <AppInitializer>
        <AppContextProvider>
          <EventEmitterContextProvider>
            <ProviderContextProvider>
              <ModalContextProvider>
                {children}
              </ModalContextProvider>
            </ProviderContextProvider>
          </EventEmitterContextProvider>
        </AppContextProvider>
      </AppInitializer>
    </>
  )
}
export default Layout
