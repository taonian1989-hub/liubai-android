package io.liubai.assistant;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.webkit.*;
import android.widget.FrameLayout;
import android.widget.Toast;
import java.io.*;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** The bridge is restricted to immutable bundled assets on a synthetic HTTPS origin. */
public class MainActivity extends Activity {
    private WebView web;
    private FrameLayout root;
    private ModelBridge bridge;
    private String pendingExport;
    private static final String HOST="app.liubai.local";
    private static final Set<String> ASSETS=new HashSet<>(Arrays.asList("index.html","app.css","app.js","quotes.js"));
    @Override public void onCreate(Bundle state){
        super.onCreate(state);
        getWindow().setStatusBarColor(Color.TRANSPARENT);getWindow().setNavigationBarColor(Color.TRANSPARENT);
        root=new FrameLayout(this);root.setBackgroundColor(Color.rgb(247,247,242));
        root.setOnApplyWindowInsetsListener((v,insets)->{v.setPadding(insets.getSystemWindowInsetLeft(),insets.getSystemWindowInsetTop(),insets.getSystemWindowInsetRight(),insets.getSystemWindowInsetBottom());return insets.consumeSystemWindowInsets();});
        web=new WebView(this);web.setBackgroundColor(Color.rgb(247,247,242));
        WebSettings s=web.getSettings();s.setJavaScriptEnabled(true);s.setDomStorageEnabled(true);s.setAllowFileAccess(false);s.setAllowContentAccess(false);s.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);s.setJavaScriptCanOpenWindowsAutomatically(false);s.setSafeBrowsingEnabled(true);
        web.setImportantForAutofill(android.view.View.IMPORTANT_FOR_AUTOFILL_NO_EXCLUDE_DESCENDANTS);
        bridge=new ModelBridge(this,web);web.addJavascriptInterface(bridge,"ModelBridge");web.addJavascriptInterface(new Device(),"Device");
        web.setWebViewClient(new WebViewClient(){
            @Override public WebResourceResponse shouldInterceptRequest(WebView view,WebResourceRequest req){
                Uri u=req.getUrl();String path=u.getPath();String name=path==null||path.equals("/")?"index.html":path.substring(1);
                if(!"https".equals(u.getScheme())||!HOST.equals(u.getHost())||!ASSETS.contains(name))return blocked();
                try{return new WebResourceResponse(name.endsWith(".js")?"application/javascript":name.endsWith(".css")?"text/css":"text/html","UTF-8",getAssets().open(name));}catch(Exception e){return blocked();}
            }
            @Override public boolean shouldOverrideUrlLoading(WebView view,WebResourceRequest req){external(req.getUrl().toString());return true;}
        });
        root.addView(web,new FrameLayout.LayoutParams(-1,-1));setContentView(root);root.requestApplyInsets();web.loadUrl("https://"+HOST+"/index.html");
    }
    private static WebResourceResponse blocked(){return new WebResourceResponse("text/plain","UTF-8",403,"Blocked",null,new ByteArrayInputStream(new byte[0]));}
    private void external(String raw){try{URI u=new URI(raw);if(("https".equals(u.getScheme())||"http".equals(u.getScheme()))&&u.getHost()!=null&&u.getRawUserInfo()==null)startActivity(new Intent(Intent.ACTION_VIEW,Uri.parse(raw)));}catch(Exception ignored){Toast.makeText(this,"无法打开该链接",Toast.LENGTH_SHORT).show();}}
    public final class Device {
        @JavascriptInterface public void theme(String value){final boolean dark="dark".equals(value);runOnUiThread(()->{int color=Color.parseColor(dark?"#19251f":"#f7f7f2");root.setBackgroundColor(color);web.setBackgroundColor(color);getWindow().getDecorView().setSystemUiVisibility(dark?0:android.view.View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR|android.view.View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR);});}
        @JavascriptInterface public void open(String url){runOnUiThread(()->external(url));}
        @JavascriptInterface public void export(String text){if(text==null||text.length()>25000000)return;runOnUiThread(()->{
            if(pendingExport!=null){Toast.makeText(MainActivity.this,"请先完成当前导出",Toast.LENGTH_SHORT).show();return;}
            pendingExport=text;Intent i=new Intent(Intent.ACTION_CREATE_DOCUMENT).setType("text/markdown").addCategory(Intent.CATEGORY_OPENABLE).putExtra(Intent.EXTRA_TITLE,"留白_研究笔记_"+new java.text.SimpleDateFormat("yyyyMMdd_HHmmss",Locale.ROOT).format(new Date())+".md");
            try{startActivityForResult(i,101);}catch(Exception e){pendingExport=null;Toast.makeText(MainActivity.this,"设备未提供文件保存入口",Toast.LENGTH_LONG).show();}
        });}
    }
    @Override protected void onActivityResult(int request,int result,Intent data){super.onActivityResult(request,result,data);if(request!=101)return;String text=pendingExport;pendingExport=null;if(result==RESULT_OK&&data!=null&&data.getData()!=null&&text!=null){try(OutputStream out=getContentResolver().openOutputStream(data.getData())){out.write(text.getBytes(StandardCharsets.UTF_8));Toast.makeText(this,"已导出 Markdown",Toast.LENGTH_SHORT).show();}catch(Exception e){Toast.makeText(this,"文件保存失败，请重试",Toast.LENGTH_LONG).show();}}}
    @Override public void onBackPressed(){web.evaluateJavascript("window.handleBack && window.handleBack()",value->{if(!"true".equals(value))MainActivity.super.onBackPressed();});}
    @Override protected void onDestroy(){bridge.close();web.removeJavascriptInterface("ModelBridge");web.removeJavascriptInterface("Device");web.destroy();super.onDestroy();}
}
